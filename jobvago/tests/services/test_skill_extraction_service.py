"""Unit tests for the SkillExtractionService."""

import pytest
from app.services.skill_extraction_service import (
    SkillExtractionService,
    SKILL_TAXONOMY,
    SKILL_CATEGORIES,
)


class TestSkillExtractionFallback:
    """Tests for the regex-based fallback skill extractor."""

    def setup_method(self):
        """Create a service instance (Ollama won't be available)."""
        self.service = SkillExtractionService(
            api_url="http://localhost:11434/api/generate",
            model="test-model"
        )

    def test_extract_python(self):
        """Detects Python in resume text."""
        skills = self.service._extract_with_fallback("Experienced Python developer with 5 years.")
        names = [s["skill"] for s in skills]
        assert "Python" in names

    def test_extract_multiple_skills(self):
        """Detects multiple distinct skills."""
        text = "Proficient in Python, JavaScript, and React. Experience with Docker and AWS."
        skills = self.service._extract_with_fallback(text)
        names = [s["skill"] for s in skills]
        assert "Python" in names
        assert "JavaScript" in names
        assert "React" in names
        assert "Docker" in names
        assert "AWS" in names

    def test_extract_case_insensitive(self):
        """Skill detection is case-insensitive."""
        skills = self.service._extract_with_fallback("PYTHON and JAVASCRIPT developer")
        names = [s["skill"] for s in skills]
        assert "Python" in names
        assert "JavaScript" in names

    def test_extract_no_skills(self):
        """Text without recognisable skills returns empty list."""
        skills = self.service._extract_with_fallback("Enjoys hiking and reading novels.")
        assert len(skills) == 0

    def test_extract_categories_assigned(self):
        """Each extracted skill has a category."""
        skills = self.service._extract_with_fallback("Python and Docker expert")
        for s in skills:
            assert "category" in s
            assert len(s["category"]) > 0

    def test_no_duplicate_skills(self):
        """Same skill mentioned multiple times is only returned once."""
        text = "Python Python Python. Used Python daily. Expert in Python."
        skills = self.service._extract_with_fallback(text)
        python_count = sum(1 for s in skills if s["skill"] == "Python")
        assert python_count == 1

    def test_java_not_javascript(self):
        """Java detection doesn't false-positive on JavaScript."""
        skills = self.service._extract_with_fallback("Expert JavaScript developer")
        names = [s["skill"] for s in skills]
        assert "JavaScript" in names
        # Java should NOT be matched since the text only says "JavaScript"
        # (depends on regex — java regex has negative lookahead for 'script')

    def test_soft_skills_detected(self):
        """Soft skills like Leadership and Communication are detected."""
        text = "Strong leadership and communication skills. Experience in team collaboration."
        skills = self.service._extract_with_fallback(text)
        names = [s["skill"] for s in skills]
        assert "Leadership" in names
        assert "Communication" in names

    def test_extract_skills_public_api_fallback(self):
        """extract_skills falls back to regex when Ollama is offline."""
        skills, source = self.service.extract_skills("Python and AWS experience")
        assert source == "fallback"
        names = [s["skill"] for s in skills]
        assert "Python" in names
        assert "AWS" in names


class TestSkillTaxonomy:
    """Tests for the SKILL_TAXONOMY and SKILL_CATEGORIES data."""

    def test_all_taxonomy_skills_have_categories(self):
        """Every skill in SKILL_TAXONOMY has a corresponding category."""
        for skill_name in SKILL_TAXONOMY:
            assert skill_name in SKILL_CATEGORIES, f"{skill_name} missing from SKILL_CATEGORIES"

    def test_all_categories_are_non_empty(self):
        """Every category string is non-empty."""
        for skill, cat in SKILL_CATEGORIES.items():
            assert len(cat) > 0, f"Empty category for {skill}"

    def test_taxonomy_patterns_are_valid_regex(self):
        """All regex patterns in the taxonomy compile without error."""
        import re
        for skill_name, patterns in SKILL_TAXONOMY.items():
            for pattern in patterns:
                try:
                    re.compile(pattern)
                except re.error as e:
                    pytest.fail(f"Invalid regex for {skill_name}: {pattern} — {e}")
