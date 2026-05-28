import re
import requests
import json
from typing import List, Dict, Tuple


# Skills keywords
SKILL_TAXONOMY: Dict[str, List[str]] = {
    # Programming languages
    "Python":           [r"\bpython\b"],
    "Java":             [r"\bjava\b(?!script)"],
    "JavaScript":       [r"\bjavascript\b", r"\bjs\b"],
    "TypeScript":       [r"\btypescript\b"],
    "C++":              [r"\bc\+\+", r"\bcplusplus\b"],
    "C#":               [r"\bc#", r"\bcsharp\b"],
    "Go":               [r"\bgolang\b", r"\b go \b"],
    "Rust":             [r"\brust\b(?! removal)"],
    "Kotlin":           [r"\bkotlin\b"],
    "Swift":            [r"\bswift\b(?! response)"],
    "Ruby":             [r"\bruby\b(?! on rails)"],
    "PHP":              [r"\bphp\b"],
    "R":                [r"\br programming\b", r"\bstatistical computing\b"],
    "MATLAB":           [r"\bmatlab\b"],
    "Scala":            [r"\bscala\b"],
    "Bash":             [r"\bbash\b", r"\bshell scripting\b"],

    # Web frameworks & libraries
    "React":            [r"\breact\.?js\b", r"\breact\b"],
    "Angular":          [r"\bangular\b"],
    "Vue.js":           [r"\bvue\.?js\b", r"\bvuejs\b"],
    "Node.js":          [r"\bnode\.?js\b"],
    "Django":           [r"\bdjango\b"],
    "Flask":            [r"\bflask\b"],
    "FastAPI":          [r"\bfastapi\b"],
    "Spring Boot":      [r"\bspring boot\b", r"\bspring framework\b"],
    "Ruby on Rails":    [r"\bruby on rails\b", r"\brails\b"],
    "Laravel":          [r"\blaravel\b"],
    "Next.js":          [r"\bnext\.?js\b"],

    # Data & AI
    "Machine Learning": [r"\bmachine learning\b", r"\bml\b"],
    "Deep Learning":    [r"\bdeep learning\b", r"\bneural network"],
    "Data Analysis":    [r"\bdata anal[ys]", r"\bdata analyst\b"],
    "Data Science":     [r"\bdata science\b", r"\bdata scientist\b"],
    "NLP":              [r"\bnlp\b", r"\bnatural language processing\b"],
    "Computer Vision":  [r"\bcomputer vision\b", r"\bimage recognition\b"],
    "TensorFlow":       [r"\btensorflow\b"],
    "PyTorch":          [r"\bpytorch\b"],
    "Pandas":           [r"\bpandas\b"],
    "NumPy":            [r"\bnumpy\b"],
    "Scikit-learn":     [r"\bscikit.learn\b", r"\bsklearn\b"],
    "Power BI":         [r"\bpower bi\b"],
    "Tableau":          [r"\btableau\b"],
    "Excel":            [r"\bexcel\b", r"\bspreadsheet\b"],
    "SQL":              [r"\bsql\b"],
    "NoSQL":            [r"\bnosql\b", r"\bmongodb\b", r"\bcassandra\b"],
    "Apache Spark":     [r"\bapache spark\b", r"\bpyspark\b"],
    "Hadoop":           [r"\bhadoop\b"],

    # Cloud & DevOps
    "AWS":              [r"\baws\b", r"\bamazon web services\b"],
    "Azure":            [r"\bazure\b", r"\bmicrosoft azure\b"],
    "Google Cloud":     [r"\bgcp\b", r"\bgoogle cloud\b"],
    "Docker":           [r"\bdocker\b"],
    "Kubernetes":       [r"\bkubernetes\b", r"\bk8s\b"],
    "CI/CD":            [r"\bci/cd\b", r"\bcontinuous integration\b", r"\bcontinuous deployment\b"],
    "Terraform":        [r"\bterraform\b"],
    "Ansible":          [r"\bansible\b"],
    "Jenkins":          [r"\bjenkins\b"],
    "Git":              [r"\bgit\b(?!hub)?", r"\bversion control\b"],
    "GitHub":           [r"\bgithub\b"],
    "Linux":            [r"\blinux\b", r"\bunix\b"],

    # Cybersecurity
    "Cybersecurity":    [r"\bcybersecurity\b", r"\binformation security\b"],
    "Penetration Testing": [r"\bpenetration test", r"\bpen test", r"\bethical hack"],
    "Network Security": [r"\bnetwork security\b", r"\bfirewall\b"],
    "SIEM":             [r"\bsiem\b"],
    "Cryptography":     [r"\bcryptograph"],

    # Databases
    "PostgreSQL":       [r"\bpostgresql\b", r"\bpostgres\b"],
    "MySQL":            [r"\bmysql\b"],
    "MongoDB":          [r"\bmongodb\b"],
    "Redis":            [r"\bredis\b"],
    "Oracle DB":        [r"\boracle db\b", r"\boracle database\b"],

    # Project Management
    "Project Management": [r"\bproject management\b", r"\bpmp\b"],
    "Agile":            [r"\bagile\b"],
    "Scrum":            [r"\bscrum\b"],
    "Kanban":           [r"\bkanban\b"],
    "JIRA":             [r"\bjira\b"],
    "Confluence":       [r"\bconfluence\b"],

    # Design
    "UI/UX Design":     [r"\bui/ux\b", r"\buser experience\b", r"\buser interface design\b"],
    "Figma":            [r"\bfigma\b"],
    "Adobe Photoshop":  [r"\bphotoshop\b"],
    "Adobe Illustrator":[r"\billustrator\b"],
    "Sketch":           [r"\bsketch\b(?! comedy)"],

    # Finance
    "Financial Analysis": [r"\bfinancial anal", r"\bfinancial modell?ing\b"],
    "Accounting":       [r"\baccounting\b", r"\baccountant\b"],
    "Auditing":         [r"\baudit\b"],
    "SAP":              [r"\bsap\b(?! story)"],
    "QuickBooks":       [r"\bquickbooks\b"],

    # Marketing
    "Digital Marketing": [r"\bdigital marketing\b"],
    "SEO":              [r"\bseo\b", r"\bsearch engine optimis"],
    "SEM":              [r"\bsem\b", r"\bsearch engine market"],
    "Content Marketing":[r"\bcontent marketing\b"],
    "Social Media":     [r"\bsocial media\b"],
    "Google Analytics": [r"\bgoogle analytics\b"],

    # Soft skills
    "Leadership":       [r"\bleadership\b", r"\bteam lead\b", r"\bmanag"],
    "Communication":    [r"\bcommunication\b", r"\bpresentation skill"],
    "Problem Solving":  [r"\bproblem.solv", r"\banalytical think"],
    "Teamwork":         [r"\bteamwork\b", r"\bcollaborat"],

    # Healthcare
    "Nursing":          [r"\bnursing\b", r"\bnurse\b"],
    "Medical Coding":   [r"\bmedical cod", r"\bicd.10\b"],
    "Healthcare Management": [r"\bhealthcare management\b"],

    # Logistics
    "Supply Chain":     [r"\bsupply chain\b"],
    "Logistics":        [r"\blogistics\b"],
    "Warehouse Management": [r"\bwarehouse\b"],
}

SKILL_CATEGORIES: Dict[str, str] = {
    "Python": "Programming", "Java": "Programming", "JavaScript": "Programming",
    "TypeScript": "Programming", "C++": "Programming", "C#": "Programming",
    "Go": "Programming", "Rust": "Programming", "Kotlin": "Programming",
    "Swift": "Programming", "Ruby": "Programming", "PHP": "Programming",
    "R": "Programming", "MATLAB": "Programming", "Scala": "Programming", "Bash": "Programming",
    "React": "Web Development", "Angular": "Web Development", "Vue.js": "Web Development",
    "Node.js": "Web Development", "Django": "Web Development", "Flask": "Web Development",
    "FastAPI": "Web Development", "Spring Boot": "Web Development",
    "Ruby on Rails": "Web Development", "Laravel": "Web Development", "Next.js": "Web Development",
    "Machine Learning": "Data & AI", "Deep Learning": "Data & AI", "Data Analysis": "Data & AI",
    "Data Science": "Data & AI", "NLP": "Data & AI", "Computer Vision": "Data & AI",
    "TensorFlow": "Data & AI", "PyTorch": "Data & AI", "Pandas": "Data & AI",
    "NumPy": "Data & AI", "Scikit-learn": "Data & AI", "Power BI": "Data & AI",
    "Tableau": "Data & AI", "Excel": "Data & AI", "SQL": "Data & AI",
    "NoSQL": "Data & AI", "Apache Spark": "Data & AI", "Hadoop": "Data & AI",
    "AWS": "Cloud & DevOps", "Azure": "Cloud & DevOps", "Google Cloud": "Cloud & DevOps",
    "Docker": "Cloud & DevOps", "Kubernetes": "Cloud & DevOps", "CI/CD": "Cloud & DevOps",
    "Terraform": "Cloud & DevOps", "Ansible": "Cloud & DevOps", "Jenkins": "Cloud & DevOps",
    "Git": "Cloud & DevOps", "GitHub": "Cloud & DevOps", "Linux": "Cloud & DevOps",
    "Cybersecurity": "Security", "Penetration Testing": "Security",
    "Network Security": "Security", "SIEM": "Security", "Cryptography": "Security",
    "PostgreSQL": "Database", "MySQL": "Database", "MongoDB": "Database",
    "Redis": "Database", "Oracle DB": "Database",
    "Project Management": "Management", "Agile": "Management", "Scrum": "Management",
    "Kanban": "Management", "JIRA": "Management", "Confluence": "Management",
    "UI/UX Design": "Design", "Figma": "Design", "Adobe Photoshop": "Design",
    "Adobe Illustrator": "Design", "Sketch": "Design",
    "Financial Analysis": "Finance", "Accounting": "Finance", "Auditing": "Finance",
    "SAP": "Finance", "QuickBooks": "Finance",
    "Digital Marketing": "Marketing", "SEO": "Marketing", "SEM": "Marketing",
    "Content Marketing": "Marketing", "Social Media": "Marketing", "Google Analytics": "Marketing",
    "Leadership": "Soft Skills", "Communication": "Soft Skills",
    "Problem Solving": "Soft Skills", "Teamwork": "Soft Skills",
    "Nursing": "Healthcare", "Medical Coding": "Healthcare",
    "Healthcare Management": "Healthcare",
    "Supply Chain": "Logistics", "Logistics": "Logistics",
    "Warehouse Management": "Logistics",
}


class SkillExtractionService:
    """
    Extracts skills from resume text.

    Strategy:
      1. If Ollama is reachable, ask DeepSeek to return a JSON list of skills.
      2. Otherwise, run the local regex-based fallback extractor.
    """

    def __init__(self, api_url: str, model: str, timeout: int = 30):
        """Initialise the skill extraction service.

        Args:
            api_url: Ollama generate API endpoint URL.
            model: Name of the LLM model to use (e.g. 'deepseek-r1:latest').
            timeout: HTTP request timeout in seconds.
        """
        self.api_url = api_url        # e.g. http://localhost:11434/api/generate
        self.model = model            # e.g. deepseek-r1:latest
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_skills(self, resume_text: str) -> Tuple[List[Dict], str]:
        """
        Extract skills from resume text.

        Returns:
            (skills, source) where skills is a list of
            {'skill': str, 'category': str} dicts and source is
            'deepseek' or 'fallback'.
        """
        if self._is_ollama_running():
            skills = self._extract_with_deepseek(resume_text)
            if skills:
                return skills, 'deepseek'

        # Fallback
        return self._extract_with_fallback(resume_text), 'fallback'

    # ------------------------------------------------------------------
    # Ollama / DeepSeek path
    # ------------------------------------------------------------------

    def _is_ollama_running(self) -> bool:
        """Check whether the Ollama server is reachable by pinging /api/tags.

        Returns:
            bool: True if the server responds with HTTP 200, False otherwise.
        """
        try:
            # Derive base URL from the generate endpoint
            base = self.api_url.replace('/api/generate', '').rstrip('/')
            r = requests.get(f"{base}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def _extract_with_deepseek(self, text: str) -> List[Dict]:
        """Send resume text to the DeepSeek model and parse returned skill JSON.

        Args:
            text: Raw resume text (truncated to 5000 chars in the prompt).

        Returns:
            list[dict]: List of {'skill': str, 'category': str} dicts, or empty on failure.
        """
        prompt = f"""You are a professional skills extractor. Read the resume below and extract ALL technical and professional skills mentioned.

Return ONLY a valid JSON array. Each element must be an object with exactly two keys:
  "skill"    : the skill name (string)
  "category" : one of Programming, Web Development, Data & AI, Cloud & DevOps, Security, Database, Management, Design, Finance, Marketing, Soft Skills, Healthcare, Logistics, Other

No markdown, no explanation, no code fences. Only the raw JSON array.

Resume:
{text[:5000]}

JSON:"""
        try:
            payload = {"model": self.model, "prompt": prompt, "stream": False}
            r = requests.post(self.api_url, json=payload, timeout=self.timeout)
            if r.status_code != 200:
                return []
            raw = r.json().get('response', '')
            raw = re.sub(r'```(?:json)?', '', raw).strip()
            skills = json.loads(raw)
            if isinstance(skills, list):
                cleaned = []
                for item in skills:
                    if isinstance(item, dict) and 'skill' in item:
                        cleaned.append({
                            'skill': str(item['skill'])[:100],
                            'category': str(item.get('category', 'Other'))[:100]
                        })
                return cleaned
        except Exception:
            pass
        return []

    # ------------------------------------------------------------------
    # Regex fallback path
    # ------------------------------------------------------------------

    def _extract_with_fallback(self, text: str) -> List[Dict]:
        """Extract skills using regex patterns from the curated SKILL_TAXONOMY.

        Iterates through all taxonomy entries and checks each pattern against
        the lowercased resume text.

        Args:
            text: Raw resume text.

        Returns:
            list[dict]: List of {'skill': str, 'category': str} dicts.
        """
        text_lower = text.lower()
        found = []
        seen = set()
        for skill_name, patterns in SKILL_TAXONOMY.items():
            if skill_name in seen:
                continue
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    found.append({
                        'skill': skill_name,
                        'category': SKILL_CATEGORIES.get(skill_name, 'Other')
                    })
                    seen.add(skill_name)
                    break
        return found