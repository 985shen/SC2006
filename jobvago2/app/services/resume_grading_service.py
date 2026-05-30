import re
import json
import requests
from typing import Dict, Any, Optional
from collections import Counter

from app.services import _fast



# Keywords
ACTION_VERBS = {
    "developed", "led", "managed", "analyzed", "created", "collaborated",
    "conducted", "performed", "implemented", "designed", "built", "launched",
    "spearheaded", "orchestrated", "optimized", "streamlined", "executed",
    "pioneered", "transformed", "achieved", "delivered", "established",
    "coordinated", "directed", "supervised", "mentored", "trained",
    "researched", "evaluated", "assessed", "improved", "increased",
    "reduced", "generated", "facilitated", "supported", "maintained",
    "administered", "organized", "planned", "oversaw", "initiated",
    "championed", "accelerated", "automated", "deployed", "engineered",
    "formulated", "identified", "integrated", "introduced", "migrated",
    "modernized", "negotiated", "partnered", "produced", "proposed",
    "resolved", "restructured", "revamped", "scaled", "secured",
    "shaped", "simplified", "strategized", "unified", "validated",
    "analysed", "organised", "recognised", "optimised",
}

AVOIDED_WORDS = {"the", "that", "which", "their", "successfully", "my", "actively"}

FILLER_THRESHOLD = 3
REPETITION_THRESHOLD = 3

LEADERSHIP_KEYWORDS = {
    "president", "vice president", "vp", "captain", "head", "chair",
    "chairperson", "director", "lead", "leader", "founder", "co-founder",
    "chief", "officer", "representative", "coordinator", "organiser",
    "organizer", "secretary", "treasurer", "committee", "board",
    "elected", "appointed", "responsible for", "overseeing",
}

EXTRACURRICULAR_KEYWORDS = {
    "club", "society", "association", "team", "competition", "championship",
    "tournament", "festival", "volunteer", "community", "sports", "athletics",
    "theatre", "theater", "debate", "hackathon", "olympiad", "conference",
    "workshop", "seminar", "council", "union", "band", "orchestra", "choir",
    "publication", "journal", "editorial",
}

COMPETENCY_KEYWORDS = {
    "analytical": [
        "investigat", "root cause", "lab procedure", "specimen", "experiment",
        "data categori", "phenomena", "systems design", "projection",
        "simulation", "statistical", "regression", "hypothesis", "feasibility",
        "decision analysis", "research", "report preparation", "reasoning",
        "analysis", "diagnos", "modelling", "modeling", "quantitative",
    ],
    "communication": [
        "presentation", "business case", "recommendation", "proposal",
        "pitch", "report", "technical documentation", "outreach",
        "volunteer management", "peer support", "event management",
        "fundraising", "conference", "debate", "seminar",
        "group discussion", "published", "drafted", "authored",
    ],
    "leadership": [
        "volunteer management", "events coordination", "conflict resolution",
        "team building", "task administration", "team representation",
        "cross-functional", "mentoring", "strategic initiative",
        "founding", "startup", "crisis management", "restructuring",
        "led", "directed", "supervised", "managed team",
    ],
    "teamwork": [
        "team supervision", "team formation", "team motivation",
        "task administration", "fundraising", "delegation",
        "project coordination", "collaboration", "outreach",
        "brainstorm", "research group", "team support",
    ],
    "initiative": [
        "counseling", "mentorship", "peer facilitation", "team training",
        "people development", "experiment methodology", "new technique",
        "features development", "r&d", "concept presentation",
        "idea presentation", "comprehensive research", "pitching",
        "hypothesis creation", "method formulation", "new system",
        "new product", "process re-engineering", "innovation",
    ],
}

ENGLISH_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "was", "are", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "i", "we", "you",
    "he", "she", "it", "they", "this", "that", "these", "those", "which",
    "who", "whom", "what", "where", "when", "how", "all", "each", "every",
    "both", "few", "more", "most", "other", "some", "such", "than", "then",
    "so", "as", "if", "while", "about", "through", "during", "before",
    "after", "above", "below", "between", "into", "out", "up", "down",
    "also", "any", "no", "not", "only", "same", "very", "just", "our",
    "their", "my", "your", "its", "his", "her", "well", "new", "use",
}


# ---------------------------------------------------------------------------
# Native keyword matchers (built once at import; case-sensitive because callers
# pass already-lowercased text, preserving exact str.lower() semantics).
# Falls back to pure Python automatically when the C++ extension is absent.
# ---------------------------------------------------------------------------
_LEADERSHIP_MATCHER = _fast.make_matcher(LEADERSHIP_KEYWORDS, case_insensitive=False)
_EXTRACURRICULAR_MATCHER = _fast.make_matcher(EXTRACURRICULAR_KEYWORDS, case_insensitive=False)
_COMPETENCY_MATCHERS = {
    cat: _fast.make_matcher(kws, case_insensitive=False)
    for cat, kws in COMPETENCY_KEYWORDS.items()
}


# Helpers
def _tokens(text: str):
    """Tokenise text into a list of lowercase alphabetical words.

    Args:
        text: Input text string.

    Returns:
        list[str]: Lowercase word tokens.
    """
    return re.findall(r"\b[a-z]+\b", text.lower())

def _sentences(text: str):
    """Split text into sentences using common punctuation delimiters.

    Args:
        text: Input text string.

    Returns:
        list[str]: Non-empty sentence fragments.
    """
    return [s.strip() for s in re.split(r"[.!?;]", text) if s.strip()]

def _bullet_lines(text: str):
    """Extract lines that begin with common bullet-point characters.

    Args:
        text: Input text string.

    Returns:
        list[str]: Stripped bullet-point lines.
    """
    lines = text.splitlines()
    return [l.strip() for l in lines
            if re.match(r"^[\u2022\-\*\u25cb\u25cf\u25a0\u2013>]\s+", l.strip())]

def _has_quantity(text: str) -> bool:
    """Check whether text contains a numeric quantity or percentage.

    Args:
        text: Input text string.

    Returns:
        bool: True if a number or percentage pattern is found.
    """
    return bool(re.search(r"\d+\s*%|\d+", text))



# Rule-based scoring
class RuleBasedScorer:
    """Deterministic, rule-based resume scoring engine.

    Provides static methods that evaluate specific resume quality dimensions
    (action verbs, quantified achievements, word repetition, contact info,
    spelling, competency keywords, etc.) and return standardised score dicts
    with points, max, and human-readable details.  No external API calls
    are required — all scoring is performed locally.
    """

    @staticmethod
    def score_action_oriented(text: str) -> Dict:
        """Score the resume on its use of strong action verbs (0-8 points).

        Args:
            text: Resume text.

        Returns:
            dict: Scoring result with points, max, found verbs, and details.
        """
        found = set(_tokens(text)) & ACTION_VERBS
        count = len(found)
        if count >= 10: pts = 8
        elif count >= 6: pts = 6
        elif count >= 3: pts = 4
        elif count >= 1: pts = 2
        else: pts = 0
        return {
            "points": pts, "max": 8,
            "found": sorted(found),
            "details": f"Found {count} distinct action verb(s).",
        }

    @staticmethod
    def score_specifics(text: str) -> Dict:
        """Score the resume on quantified achievements in bullet points (0-8 points).

        Args:
            text: Resume text.

        Returns:
            dict: Scoring result with points, max, counts, and details.
        """
        bullets = _bullet_lines(text) or _sentences(text)
        if not bullets:
            return {"points": 0, "max": 8, "quantified": 0, "total": 0,
                    "details": "No bullet points detected."}
        quantified = sum(1 for b in bullets if _has_quantity(b))
        ratio = quantified / len(bullets)
        if ratio >= 0.6: pts = 8
        elif ratio >= 0.4: pts = 6
        elif ratio >= 0.2: pts = 4
        elif quantified > 0: pts = 2
        else: pts = 0
        return {
            "points": pts, "max": 8,
            "quantified": quantified, "total": len(bullets),
            "details": f"{quantified} of {len(bullets)} bullet(s) contain numbers/metrics.",
        }

    @staticmethod
    def score_over_usage(text: str) -> Dict:
        """Penalise excessive repetition of content words (0-6 points).

        Args:
            text: Resume text.

        Returns:
            dict: Scoring result with points, max, repeated words, and details.
        """
        tokens = _tokens(text)
        content = [t for t in tokens if t not in ENGLISH_STOPWORDS and len(t) > 3]
        freq = Counter(content)
        repeated = {w: c for w, c in freq.items() if c > REPETITION_THRESHOLD}
        count = len(repeated)
        if count == 0: pts = 6
        elif count <= 2: pts = 4
        elif count <= 4: pts = 2
        else: pts = 0
        top = sorted(repeated.items(), key=lambda x: -x[1])[:5]
        return {
            "points": pts, "max": 6,
            "repeated_words": top,
            "details": f"{count} word(s) used more than {REPETITION_THRESHOLD} times.",
        }

    @staticmethod
    def score_avoided_words(text: str) -> Dict:
        """Penalise overuse of filler and avoided words (0-6 points).

        Args:
            text: Resume text.

        Returns:
            dict: Scoring result with points, max, flagged words, and details.
        """
        freq = Counter(_tokens(text))
        flagged = {w: freq[w] for w in AVOIDED_WORDS if freq.get(w, 0) > FILLER_THRESHOLD}
        count = len(flagged)
        if count == 0: pts = 6
        elif count == 1: pts = 4
        elif count == 2: pts = 2
        else: pts = 0
        return {
            "points": pts, "max": 6,
            "flagged_words": flagged,
            "details": f"{count} filler word(s) overused.",
        }

    @staticmethod
    def score_page_count(page_count: int) -> Dict:
        """Score the resume based on page length (0-10 points).

        Args:
            page_count: Number of pages in the resume PDF.

        Returns:
            dict: Scoring result with points, max, page count, and details.
        """
        if page_count <= 2: pts = 10
        elif page_count == 3: pts = 5
        else: pts = 0
        return {
            "points": pts, "max": 10,
            "pages": page_count,
            "details": f"Resume is {page_count} page(s).",
        }

    @staticmethod
    def score_contact_info(text: str) -> Dict:
        """Score the presence of phone number and email address (0-10 points).

        Args:
            text: Resume text.

        Returns:
            dict: Scoring result with points, max, detection flags, and details.
        """
        has_phone = bool(re.search(r"(\+?\d[\d\s\-().]{7,}\d|\b\d{8,}\b)", text))
        has_email = bool(re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text))
        pts = (5 if has_phone else 0) + (5 if has_email else 0)
        return {
            "points": pts, "max": 10,
            "has_phone": has_phone, "has_email": has_email,
            "details": f"Phone: {'found' if has_phone else 'missing'}  |  Email: {'found' if has_email else 'missing'}",
        }

    @staticmethod
    def score_spell_check(text: str) -> Dict:
        """Score the resume on spelling accuracy (0-10 points).

        Uses pyspellchecker if available; awards partial credit otherwise.

        Args:
            text: Resume text.

        Returns:
            dict: Scoring result with points, max, error list, and details.
        """
        try:
            from spellchecker import SpellChecker
            spell = SpellChecker()
            words = re.findall(r"\b[a-zA-Z]{3,}\b", text)
            filtered = [w for w in words if w == w.lower()]
            false_positives = {
                "spearheaded", "optimised", "organising", "analysed",
                "organisations", "programmes", "modelling", "recognised",
                "skillset", "skillsets",
            }
            misspelled = spell.unknown(filtered) - false_positives
            count = len(misspelled)
            if count == 0: pts = 10
            elif count <= 2: pts = 7
            elif count <= 5: pts = 4
            else: pts = 0
            return {
                "points": pts, "max": 10,
                "errors": sorted(list(misspelled))[:10],
                "details": f"{count} potential spelling error(s) found.",
            }
        except ImportError:
            return {
                "points": 7, "max": 10, "errors": [],
                "details": "Spell check unavailable. Partial credit awarded.",
            }

    @staticmethod
    def score_competency(text: str, category: str) -> Dict:
        """Score evidence of a specific competency category via keyword matching (0-6 points).

        Args:
            text: Resume text.
            category: Competency category key (e.g. 'analytical', 'leadership').

        Returns:
            dict: Scoring result with points, max, matched keywords, and details.
        """
        keywords = COMPETENCY_KEYWORDS.get(category, [])
        text_lower = text.lower()
        matcher = _COMPETENCY_MATCHERS.get(category)
        found = matcher.match_unique(text_lower) if matcher is not None else []
        count = len(found)
        if count >= 4: pts = 6
        elif count >= 3: pts = 5
        elif count >= 2: pts = 3
        elif count >= 1: pts = 1
        else: pts = 0
        return {
            "points": pts, "max": 6,
            "matched_keywords": found[:8],
            "details": f"{count} keyword(s) matched for {category} skills.",
            "ai_graded": False,
        }


# Score using deepseek
class AIScorer:
    """AI-powered resume scoring engine backed by Ollama / DeepSeek.

    Sends structured prompts to the LLM to evaluate leadership, extra-curricular
    activities, and individual competency categories.  Each scoring method
    includes an automatic keyword-based fallback that activates when the AI
    backend is unreachable or returns unparseable output.
    """

    def __init__(self, api_url: str, model: str, timeout: int = 45):
        """Initialise the AI scorer with Ollama connection details.

        Args:
            api_url: Ollama generate API endpoint URL.
            model: LLM model name to use.
            timeout: HTTP request timeout in seconds.
        """
        self.api_url = api_url
        self.model = model
        self.timeout = timeout

    def is_online(self) -> bool:
        """Check whether the Ollama server is reachable.

        Returns:
            bool: True if the server responds successfully.
        """
        try:
            base = self.api_url.replace("/api/generate", "").rstrip("/")
            r = requests.get(f"{base}/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def _call(self, prompt: str) -> Optional[str]:
        """Send a prompt to the Ollama generate API and return the response text.

        Args:
            prompt: The full prompt string to send.

        Returns:
            str | None: The model's response text, or None on failure.
        """
        try:
            payload = {"model": self.model, "prompt": prompt, "stream": False}
            r = requests.post(self.api_url, json=payload, timeout=self.timeout)
            if r.status_code == 200:
                return r.json().get("response", "")
        except Exception:
            pass
        return None

    def _parse_json(self, raw: Optional[str]) -> Optional[Dict]:
        """Extract and parse the first JSON object from raw model output.

        Strips markdown code fences before attempting to parse.

        Args:
            raw: Raw response string from the model.

        Returns:
            dict | None: Parsed JSON object, or None on failure.
        """
        if not raw:
            return None
        try:
            clean = re.sub(r"```json|```", "", raw).strip()
            m = re.search(r"\{.*?\}", clean, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception:
            pass
        return None

    def score_positions_of_responsibility(self, text: str) -> Dict:
        """Score leadership and positions of responsibility using AI (0-6 points).

        Falls back to keyword-based scoring if the AI call fails.

        Args:
            text: Resume text.

        Returns:
            dict: Scoring result with points, max, details, and ai_graded flag.
        """
        prompt = (
            "You are an expert resume reviewer assessing leadership and positions of responsibility.\n\n"
            "Read the resume below. Evaluate whether the candidate demonstrates clear leadership roles.\n"
            "Look for: named titles, team sizes, specific responsibilities, quantified impact.\n\n"
            f"Resume:\n{text[:3000]}\n\n"
            'Respond ONLY with valid JSON, no markdown fences, no extra text:\n'
            '{"points": <integer 0-6>, "details": "<one concise sentence>"}\n\n'
            "Scoring: 0=no leadership, 2=vague mentions, 4=clear roles, 6=strong roles with quantified impact."
        )
        data = self._parse_json(self._call(prompt))
        if data:
            return {
                "points": max(0, min(6, int(data.get("points", 3)))),
                "max": 6, "details": data.get("details", ""), "ai_graded": True,
            }
        return self._fallback_positions(text)

    def _fallback_positions(self, text: str) -> Dict:
        """Rule-based fallback scorer for leadership positions (0-6 points).

        Args:
            text: Resume text.

        Returns:
            dict: Scoring result with points, max, and details.
        """
        text_lower = text.lower()
        count = _LEADERSHIP_MATCHER.count_matches(text_lower)
        pts = 6 if count >= 4 else (4 if count >= 2 else (2 if count >= 1 else 0))
        return {
            "points": pts, "max": 6,
            "details": f"Rule-based fallback: {count} leadership indicator(s) found.",
            "ai_graded": False,
        }

    def score_extracurricular(self, text: str) -> Dict:
        """Score extra-curricular activities using AI (0-6 points).

        Falls back to keyword-based scoring if the AI call fails.

        Args:
            text: Resume text.

        Returns:
            dict: Scoring result with points, max, details, and ai_graded flag.
        """
        prompt = (
            "You are an expert resume reviewer assessing extra-curricular activities.\n\n"
            "Read the resume. Evaluate whether extra-curricular entries are well-described.\n"
            "Look for: specific competition/club name, candidate role, duration, achievements.\n\n"
            f"Resume:\n{text[:3000]}\n\n"
            'Respond ONLY with valid JSON, no markdown fences, no extra text:\n'
            '{"points": <integer 0-6>, "details": "<one concise sentence>"}\n\n'
            "Scoring: 0=none, 2=listed but vague, 4=reasonable detail, 6=rich detail with role+achievement."
        )
        data = self._parse_json(self._call(prompt))
        if data:
            return {
                "points": max(0, min(6, int(data.get("points", 3)))),
                "max": 6, "details": data.get("details", ""), "ai_graded": True,
            }
        return self._fallback_extracurricular(text)

    def _fallback_extracurricular(self, text: str) -> Dict:
        """Rule-based fallback scorer for extra-curricular activities (0-6 points).

        Args:
            text: Resume text.

        Returns:
            dict: Scoring result with points, max, and details.
        """
        text_lower = text.lower()
        count = _EXTRACURRICULAR_MATCHER.count_matches(text_lower)
        pts = 5 if count >= 4 else (3 if count >= 2 else (1 if count >= 1 else 0))
        return {
            "points": pts, "max": 6,
            "details": f"Rule-based fallback: {count} extra-curricular indicator(s) found.",
            "ai_graded": False,
        }

    def score_competency_ai(self, text: str, category: str) -> Dict:
        """Score a specific competency category using AI (0-6 points).

        Falls back to RuleBasedScorer.score_competency if the AI call fails.

        Args:
            text: Resume text.
            category: Competency category key (e.g. 'analytical').

        Returns:
            dict: Scoring result with points, max, details, and ai_graded flag.
        """
        prompt = (
            f"You are an expert resume reviewer assessing {category} skills.\n\n"
            f"Read the resume and score the evidence of {category} skills shown.\n\n"
            f"Resume:\n{text[:3000]}\n\n"
            'Respond ONLY with valid JSON, no markdown fences, no extra text:\n'
            '{"points": <integer 0-6>, "details": "<one concise sentence>"}\n\n'
            "Scoring: 0=no evidence, 2=weak/implicit, 4=moderate evidence, 6=strong with impact."
        )
        data = self._parse_json(self._call(prompt))
        if data:
            return {
                "points": max(0, min(6, int(data.get("points", 3)))),
                "max": 6, "details": data.get("details", ""), "ai_graded": True,
            }
        return RuleBasedScorer.score_competency(text, category)


# Grade resume out of 100 points
class ResumeGradingService:
    """
    Hybrid resume grader — 100 point scale.

    Score breakdown:
      Impact        40 pts:
        action_oriented          8  (rule-based)
        specifics                8  (rule-based)
        over_usage               6  (rule-based)
        avoided_words            6  (rule-based)
        positions_of_resp        6  (AI / rule fallback)
        extracurricular          6  (AI / rule fallback)

      Presentation  30 pts:
        page_count              10  (rule-based)
        contact_info            10  (rule-based)
        spell_check             10  (rule-based)

      Competencies  30 pts:
        analytical               6  (AI / rule fallback)
        communication            6  (AI / rule fallback)
        leadership               6  (AI / rule fallback)
        teamwork                 6  (AI / rule fallback)
        initiative               6  (AI / rule fallback)
    """

    COMPETENCY_CATEGORIES = [
        "analytical", "communication", "leadership", "teamwork", "initiative"
    ]

    def __init__(self, ollama_url: str, model: str, timeout: int = 45):
        """Initialise the grading service with an AI scorer backend.

        Args:
            ollama_url: Ollama generate API endpoint URL.
            model: LLM model name to use.
            timeout: HTTP request timeout in seconds.
        """
        self.ai = AIScorer(ollama_url, model, timeout)

    def grade(self, text: str, page_count: int = 1) -> Dict[str, Any]:
        """Grade a resume on a 100-point scale across impact, presentation, and competencies.

        Uses a hybrid approach combining rule-based heuristics and AI scoring
        (when Ollama is available).  Falls back to pure rule-based scoring if
        the AI backend is offline.

        Args:
            text: Full resume text extracted from the PDF.
            page_count: Number of pages in the resume PDF.

        Returns:
            dict: Structured grading result containing total score, per-section
                  scores and breakdowns, and an ollama_online flag.
        """
        ollama_online = self.ai.is_online()

        # Impact
        action    = RuleBasedScorer.score_action_oriented(text)
        specifics = RuleBasedScorer.score_specifics(text)
        over_use  = RuleBasedScorer.score_over_usage(text)
        avoided   = RuleBasedScorer.score_avoided_words(text)

        if ollama_online:
            pos_resp   = self.ai.score_positions_of_responsibility(text)
            extra_curr = self.ai.score_extracurricular(text)
        else:
            pos_resp   = self.ai._fallback_positions(text)
            extra_curr = self.ai._fallback_extracurricular(text)

        impact_score = min(
            action["points"] + specifics["points"] + over_use["points"] +
            avoided["points"] + pos_resp["points"] + extra_curr["points"],
            40
        )

        # Presentation
        pages   = RuleBasedScorer.score_page_count(page_count)
        contact = RuleBasedScorer.score_contact_info(text)
        spell   = RuleBasedScorer.score_spell_check(text)
        presentation_score = min(
            pages["points"] + contact["points"] + spell["points"], 30
        )

        # Competencies
        comp_results = {}
        for cat in self.COMPETENCY_CATEGORIES:
            if ollama_online:
                comp_results[cat] = self.ai.score_competency_ai(text, cat)
            else:
                comp_results[cat] = RuleBasedScorer.score_competency(text, cat)

        competencies_score = min(
            sum(r["points"] for r in comp_results.values()), 30
        )

        total = impact_score + presentation_score + competencies_score

        return {
            "total": total,
            "ollama_online": ollama_online,
            "impact": {
                "score": impact_score,
                "max": 40,
                "breakdown": {
                    "action_oriented": action,
                    "specifics": specifics,
                    "over_usage": over_use,
                    "avoided_words": avoided,
                    "positions_of_responsibility": pos_resp,
                    "extracurricular": extra_curr,
                },
            },
            "presentation": {
                "score": presentation_score,
                "max": 30,
                "breakdown": {
                    "page_count": pages,
                    "contact_info": contact,
                    "spell_check": spell,
                },
            },
            "competencies": {
                "score": competencies_score,
                "max": 30,
                "breakdown": comp_results,
            },
        }
