"""Unit tests for the resume grading service — rule-based scorers and helpers."""

import pytest
from app.services.resume_grading_service import (
    RuleBasedScorer,
    AIScorer,
    ResumeGradingService,
    _tokens,
    _sentences,
    _bullet_lines,
    _has_quantity,
)


class TestHelperFunctions:
    """Tests for module-level helper functions."""

    def test_tokens_basic(self):
        """_tokens splits text into lowercase words."""
        result = _tokens("Hello World Python")
        assert result == ["hello", "world", "python"]

    def test_tokens_strips_punctuation(self):
        """_tokens ignores non-alphabetical characters."""
        result = _tokens("Built 3 APIs, deployed 2 services!")
        assert "built" in result
        assert "apis" in result
        assert "3" not in result

    def test_sentences_basic(self):
        """_sentences splits on punctuation."""
        result = _sentences("First sentence. Second sentence! Third?")
        assert len(result) == 3

    def test_sentences_empty(self):
        """_sentences returns empty list for empty input."""
        assert _sentences("") == []

    def test_bullet_lines_detects_bullets(self):
        """_bullet_lines extracts lines starting with bullet characters."""
        text = "Header\n• First bullet\n• Second bullet\nPlain line\n- Dash bullet"
        result = _bullet_lines(text)
        assert len(result) == 3

    def test_bullet_lines_no_bullets(self):
        """_bullet_lines returns empty list when no bullets exist."""
        assert _bullet_lines("Just a plain paragraph.") == []

    def test_has_quantity_with_number(self):
        """_has_quantity detects numbers."""
        assert _has_quantity("Increased revenue by 30%") is True
        assert _has_quantity("Managed team of 12") is True

    def test_has_quantity_without_number(self):
        """_has_quantity returns False for text without numbers."""
        assert _has_quantity("Led the marketing team") is False


class TestScoreActionOriented:
    """Tests for RuleBasedScorer.score_action_oriented."""

    def test_many_action_verbs(self):
        """Resume with many action verbs scores high."""
        text = "developed led managed analyzed created implemented designed built launched optimized streamlined executed"
        result = RuleBasedScorer.score_action_oriented(text)
        assert result["points"] == 8
        assert result["max"] == 8
        assert len(result["found"]) >= 10

    def test_few_action_verbs(self):
        """Resume with few action verbs scores lower."""
        text = "I developed a website and managed a team."
        result = RuleBasedScorer.score_action_oriented(text)
        assert 0 < result["points"] < 8
        assert "developed" in result["found"]
        assert "managed" in result["found"]

    def test_no_action_verbs(self):
        """Resume with no action verbs scores zero."""
        text = "I was responsible for the project. I worked on things."
        result = RuleBasedScorer.score_action_oriented(text)
        assert result["points"] == 0
        assert len(result["found"]) == 0


class TestScoreSpecifics:
    """Tests for RuleBasedScorer.score_specifics."""

    def test_quantified_bullets(self):
        """Bullets with numbers score higher."""
        text = "• Increased revenue by 30%\n• Managed team of 12\n• Reduced costs by 15%"
        result = RuleBasedScorer.score_specifics(text)
        assert result["points"] > 0
        assert result["quantified"] == 3

    def test_no_quantified_bullets(self):
        """Bullets without numbers score zero."""
        text = "• Led the team\n• Managed projects\n• Worked on deliverables"
        result = RuleBasedScorer.score_specifics(text)
        assert result["quantified"] == 0
        assert result["points"] == 0

    def test_empty_text(self):
        """Empty text returns zero."""
        result = RuleBasedScorer.score_specifics("")
        assert result["points"] == 0


class TestScoreOverUsage:
    """Tests for RuleBasedScorer.score_over_usage."""

    def test_no_repetition(self):
        """Text with varied vocabulary scores full marks."""
        text = "Developed software. Managed team. Designed architecture. Built systems."
        result = RuleBasedScorer.score_over_usage(text)
        assert result["points"] == 6

    def test_heavy_repetition(self):
        """Text repeating the same word excessively scores low."""
        text = "project " * 20 + "management " * 20 + "development " * 20 + "system " * 20 + "analysis " * 20
        result = RuleBasedScorer.score_over_usage(text)
        assert result["points"] < 6


class TestScoreAvoidedWords:
    """Tests for RuleBasedScorer.score_avoided_words."""

    def test_no_filler_words(self):
        """Text without filler words scores full marks."""
        text = "Developed an API. Led project delivery. Managed stakeholders."
        result = RuleBasedScorer.score_avoided_words(text)
        assert result["points"] == 6

    def test_excessive_filler_words(self):
        """Text overusing filler words scores low."""
        text = ("successfully successfully successfully successfully "
                "actively actively actively actively "
                "the the the the the")
        result = RuleBasedScorer.score_avoided_words(text)
        assert result["points"] < 6


class TestScorePageCount:
    """Tests for RuleBasedScorer.score_page_count."""

    def test_one_page(self):
        """A 1-page resume gets full marks."""
        result = RuleBasedScorer.score_page_count(1)
        assert result["points"] == 10

    def test_two_pages(self):
        """A 2-page resume gets full marks."""
        result = RuleBasedScorer.score_page_count(2)
        assert result["points"] == 10

    def test_three_pages(self):
        """A 3-page resume gets partial marks."""
        result = RuleBasedScorer.score_page_count(3)
        assert result["points"] == 5

    def test_four_pages(self):
        """A 4+ page resume gets zero."""
        result = RuleBasedScorer.score_page_count(4)
        assert result["points"] == 0


class TestScoreContactInfo:
    """Tests for RuleBasedScorer.score_contact_info."""

    def test_both_phone_and_email(self):
        """Text with both phone and email gets full marks."""
        text = "John Doe | john@example.com | +65 91234567"
        result = RuleBasedScorer.score_contact_info(text)
        assert result["points"] == 10
        assert result["has_phone"] is True
        assert result["has_email"] is True

    def test_email_only(self):
        """Text with only email gets partial marks."""
        text = "Contact: john@example.com"
        result = RuleBasedScorer.score_contact_info(text)
        assert result["points"] == 5
        assert result["has_email"] is True
        assert result["has_phone"] is False

    def test_no_contact_info(self):
        """Text without contact info gets zero."""
        text = "Some resume content without any contact details."
        result = RuleBasedScorer.score_contact_info(text)
        assert result["points"] == 0


class TestScoreCompetency:
    """Tests for RuleBasedScorer.score_competency."""

    def test_analytical_skills_present(self):
        """Text with analytical keywords scores points."""
        text = "Conducted research and statistical analysis. Built regression models and simulation."
        result = RuleBasedScorer.score_competency(text, "analytical")
        assert result["points"] > 0
        assert len(result["matched_keywords"]) > 0

    def test_no_matching_keywords(self):
        """Text without relevant keywords scores zero."""
        text = "Went to the store and bought groceries."
        result = RuleBasedScorer.score_competency(text, "analytical")
        assert result["points"] == 0

    def test_invalid_category(self):
        """An unknown category returns zero matches."""
        text = "Some resume text with various skills."
        result = RuleBasedScorer.score_competency(text, "nonexistent_category")
        assert result["points"] == 0


class TestAIScorerFallbacks:
    """Tests for AIScorer fallback methods (no Ollama needed)."""

    def test_fallback_positions_with_keywords(self):
        """Fallback detects leadership keywords."""
        scorer = AIScorer("http://localhost:11434/api/generate", "test-model")
        text = "President of the Engineering Club. Vice president of student council. Led 30 members."
        result = scorer._fallback_positions(text)
        assert result["points"] > 0
        assert result["ai_graded"] is False

    def test_fallback_positions_no_keywords(self):
        """Fallback returns zero when no leadership keywords found."""
        scorer = AIScorer("http://localhost:11434/api/generate", "test-model")
        text = "Studied mathematics and completed assignments."
        result = scorer._fallback_positions(text)
        assert result["points"] == 0

    def test_fallback_extracurricular_with_keywords(self):
        """Fallback detects extra-curricular keywords."""
        scorer = AIScorer("http://localhost:11434/api/generate", "test-model")
        text = "Member of robotics club. Participated in hackathon and debate competition. Volunteered at community events."
        result = scorer._fallback_extracurricular(text)
        assert result["points"] > 0

    def test_fallback_extracurricular_no_keywords(self):
        """Fallback returns zero when no extra-curricular keywords found."""
        scorer = AIScorer("http://localhost:11434/api/generate", "test-model")
        text = "Completed all coursework on time."
        result = scorer._fallback_extracurricular(text)
        assert result["points"] == 0

    def test_parse_json_valid(self):
        """_parse_json parses a valid JSON string."""
        scorer = AIScorer("http://localhost:11434/api/generate", "test-model")
        result = scorer._parse_json('{"points": 5, "details": "Good"}')
        assert result == {"points": 5, "details": "Good"}

    def test_parse_json_with_fences(self):
        """_parse_json strips markdown code fences."""
        scorer = AIScorer("http://localhost:11434/api/generate", "test-model")
        result = scorer._parse_json('```json\n{"points": 3}\n```')
        assert result is not None
        assert result["points"] == 3

    def test_parse_json_invalid(self):
        """_parse_json returns None for invalid input."""
        scorer = AIScorer("http://localhost:11434/api/generate", "test-model")
        assert scorer._parse_json("not json at all") is None
        assert scorer._parse_json(None) is None
        assert scorer._parse_json("") is None


class TestResumeGradingService:
    """Tests for the full grading pipeline."""

    def test_grade_returns_complete_structure(self):
        """grade() returns all required keys and sub-scores."""
        service = ResumeGradingService(
            ollama_url="http://localhost:11434/api/generate",
            model="test-model"
        )
        text = """
        John Doe | john@example.com | +65 91234567

        WORK EXPERIENCE
        Software Engineer, Acme Corp
        • Developed RESTful APIs serving 10,000 daily requests
        • Led migration of legacy system to microservices architecture
        • Reduced deployment time by 40% through CI/CD automation
        • Managed team of 5 junior developers

        EDUCATION
        BSc Computer Science, National University of Singapore

        SKILLS
        Python, Java, Docker, Kubernetes, AWS
        """
        result = service.grade(text, page_count=1)

        assert "total" in result
        assert "impact" in result
        assert "presentation" in result
        assert "competencies" in result
        assert result["impact"]["max"] == 40
        assert result["presentation"]["max"] == 30
        assert result["competencies"]["max"] == 30
        assert 0 <= result["total"] <= 100

    def test_grade_scores_within_bounds(self):
        """All sub-scores are within their maximum bounds."""
        service = ResumeGradingService(
            ollama_url="http://localhost:11434/api/generate",
            model="test-model"
        )
        result = service.grade("Some basic resume text.", page_count=1)

        assert 0 <= result["impact"]["score"] <= 40
        assert 0 <= result["presentation"]["score"] <= 30
        assert 0 <= result["competencies"]["score"] <= 30
        assert result["total"] == (
            result["impact"]["score"] +
            result["presentation"]["score"] +
            result["competencies"]["score"]
        )

    def test_grade_empty_text(self):
        """Grading empty text doesn't crash."""
        service = ResumeGradingService(
            ollama_url="http://localhost:11434/api/generate",
            model="test-model"
        )
        result = service.grade("", page_count=1)
        assert result["total"] >= 0
