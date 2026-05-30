"""Unit tests for DataService helper methods."""

import pytest
from app.models.career import Industry, Course, DashboardStats
from app.services.data_service import DataService

class TestDataServiceHelpers:
    """Tests for DataService internal helper methods."""

    def setup_method(self):
        """Create a DataService instance for testing."""
        self.service = DataService(
            jobs_api_url="https://example.com/jobs",
            courses_api_url="https://example.com/courses"
        )

    def test_get_industry_keywords_known(self):
        """Known industry returns keywords."""
        kw = self.service._get_industry_keywords("information technology")
        assert len(kw) > 0
        assert "python" in kw
        assert "software" in kw

    def test_get_industry_keywords_partial_match(self):
        """Partial industry name matches."""
        kw = self.service._get_industry_keywords("healthcare")
        assert len(kw) > 0
        assert "medical" in kw or "health" in kw

    def test_get_industry_keywords_unknown(self):
        """Unknown industry returns empty list."""
        kw = self.service._get_industry_keywords("underwater basket weaving")
        assert kw == []

    def test_get_industry_keywords_none(self):
        """None input returns empty list."""
        kw = self.service._get_industry_keywords(None)
        assert kw == []

    def test_extract_skills_from_title_match(self):
        """Title with known keywords produces skill tags."""
        skills = self.service._extract_skills_from_title("Advanced Python for Data Analytics")
        assert "Python" in skills
        assert "Data" in skills or "Analytics" in skills

    def test_extract_skills_from_title_no_match(self):
        """Title without known keywords returns default."""
        skills = self.service._extract_skills_from_title("Introduction to Basket Weaving")
        assert skills == ["Professional Development"]

    def test_extract_skills_max_four(self):
        """At most 4 skill tags are returned."""
        skills = self.service._extract_skills_from_title(
            "Python Java Data Cloud AI Machine Learning Design Marketing Management"
        )
        assert len(skills) <= 4

    def test_apply_filters_no_filters(self):
        """No filters returns the original list unchanged."""
        courses = [
            Course("A", "P", "10h", "Part-time", 4.0, 50, 500, 100, "80%", "High Impact", ["X"]),
            Course("B", "P", "20h", "Full-time", 3.5, 30, 300, 60, "80%", "Low Impact", ["Y"]),
        ]
        result = self.service._apply_filters(courses, None)
        assert len(result) == 2

    def test_apply_filters_by_impact(self):
        """Impact filter keeps only matching courses."""
        courses = [
            Course("A", "P", "10h", "PT", 4.0, 50, 500, 100, "80%", "High Impact", ["X"]),
            Course("B", "P", "20h", "FT", 3.5, 30, 300, 60, "80%", "Low Impact", ["Y"]),
            Course("C", "P", "15h", "PT", 4.2, 40, 400, 80, "80%", "High Impact", ["Z"]),
        ]
        result = self.service._apply_filters(courses, {"impact_level": "High Impact"})
        assert len(result) == 2
        assert all("High" in c.impact_level for c in result)

    def test_apply_filters_by_mode(self):
        """Mode filter keeps only matching courses."""
        courses = [
            Course("A", "P", "10h", "Part-time", 4.0, 50, 500, 100, "80%", "High", ["X"]),
            Course("B", "P", "20h", "Full-time", 3.5, 30, 300, 60, "80%", "Low", ["Y"]),
        ]
        result = self.service._apply_filters(courses, {"mode": "Part-time"})
        assert len(result) == 1
        assert result[0].title == "A"

    def test_apply_filters_sort_by_rating(self):
        """Sorting by rating orders highest first."""
        courses = [
            Course("Low", "P", "10h", "PT", 3.0, 50, 500, 100, "80%", "High", ["X"]),
            Course("High", "P", "10h", "PT", 5.0, 50, 500, 100, "80%", "High", ["X"]),
            Course("Mid", "P", "10h", "PT", 4.0, 50, 500, 100, "80%", "High", ["X"]),
        ]
        result = self.service._apply_filters(courses, {"sort_by": "Highest Rating"})
        assert result[0].title == "High"
        assert result[-1].title == "Low"

    def test_apply_filters_sort_by_price(self):
        """Sorting by price orders lowest first."""
        courses = [
            Course("Expensive", "P", "10h", "PT", 4.0, 50, 500, 500, "0%", "High", ["X"]),
            Course("Cheap", "P", "10h", "PT", 4.0, 50, 500, 50, "90%", "High", ["X"]),
        ]
        result = self.service._apply_filters(courses, {"sort_by": "Lowest Price"})
        assert result[0].title == "Cheap"

    def test_apply_filters_all_levels_ignored(self):
        """'All Impact Levels' filter does not restrict results."""
        courses = [
            Course("A", "P", "10h", "PT", 4.0, 50, 500, 100, "80%", "High Impact", ["X"]),
            Course("B", "P", "20h", "FT", 3.5, 30, 300, 60, "80%", "Low Impact", ["Y"]),
        ]
        result = self.service._apply_filters(courses, {"impact_level": "All Impact Levels"})
        assert len(result) == 2
