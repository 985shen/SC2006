"""Unit tests for the industry_keywords module."""

import pytest
from app.services.industry_keywords import INDUSTRY_KEYWORDS, get_industry_keywords


class TestIndustryKeywordsRegistry:
    """Tests for the INDUSTRY_KEYWORDS data structure."""

    def test_registry_is_non_empty(self):
        """The keyword registry contains at least one industry."""
        assert len(INDUSTRY_KEYWORDS) > 0

    def test_all_industries_have_keywords_list(self):
        """Every industry entry has a 'keywords' list."""
        for industry, data in INDUSTRY_KEYWORDS.items():
            assert 'keywords' in data, f"'{industry}' missing 'keywords' key"
            assert isinstance(data['keywords'], list)
            assert len(data['keywords']) > 0, f"'{industry}' has empty keywords"

    def test_known_industries_present(self):
        """Key industries are present in the registry."""
        expected = [
            'information technology', 'healthcare', 'financial',
            'engineering', 'logistics', 'sales', 'marketing',
            'education', 'hospitality', 'manufacturing',
            'creative', 'construction',
        ]
        for industry in expected:
            assert industry in INDUSTRY_KEYWORDS, f"'{industry}' not in registry"

    def test_all_keywords_are_non_empty_strings(self):
        """Every keyword is a non-empty string."""
        for industry, data in INDUSTRY_KEYWORDS.items():
            for kw in data['keywords']:
                assert isinstance(kw, str)
                assert len(kw) > 0


class TestGetIndustryKeywords:
    """Tests for the get_industry_keywords lookup function."""

    def test_exact_match(self):
        """Exact industry name returns its keywords."""
        kw = get_industry_keywords("information technology")
        assert len(kw) > 0
        assert "python" in kw
        assert "software" in kw

    def test_partial_match_substring(self):
        """An industry name that contains a registry key matches."""
        kw = get_industry_keywords("healthcare")
        assert len(kw) > 0
        assert "medical" in kw or "health" in kw

    def test_partial_match_word_overlap(self):
        """Word-level partial match works when substring match fails."""
        kw = get_industry_keywords("financial services")
        assert len(kw) > 0
        assert "finance" in kw or "financial" in kw

    def test_unknown_industry_returns_empty(self):
        """An unknown industry returns an empty list."""
        kw = get_industry_keywords("underwater basket weaving")
        assert kw == []

    def test_none_returns_empty(self):
        """None input returns an empty list."""
        kw = get_industry_keywords(None)
        assert kw == []

    def test_empty_string_returns_empty(self):
        """Empty string returns an empty list."""
        kw = get_industry_keywords("")
        assert kw == []

    def test_case_insensitive(self):
        """Lookup is case-insensitive."""
        kw = get_industry_keywords("HEALTHCARE")
        assert len(kw) > 0
