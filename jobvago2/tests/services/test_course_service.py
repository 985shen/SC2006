"""Unit tests for the CourseService."""

import pytest
from app.models.career import Course
from app.services.course_service import CourseService


class TestExtractSkillsFromTitle:
    """Tests for CourseService._extract_skills_from_title."""

    def test_match_single_keyword(self):
        """A title with one keyword returns that skill."""
        skills = CourseService._extract_skills_from_title("Advanced Python Programming")
        assert "Python" in skills

    def test_match_multiple_keywords(self):
        """A title with several keywords returns multiple skills."""
        skills = CourseService._extract_skills_from_title(
            "Python for Data Analytics"
        )
        assert "Python" in skills
        assert "Data" in skills or "Analytics" in skills

    def test_no_match_returns_default(self):
        """A title with no known keywords returns the default."""
        skills = CourseService._extract_skills_from_title(
            "Introduction to Basket Weaving"
        )
        assert skills == ["Professional Development"]

    def test_max_four_skills(self):
        """At most 4 skill tags are returned."""
        skills = CourseService._extract_skills_from_title(
            "Python Java Data Cloud AI Machine Learning Design Marketing Management"
        )
        assert len(skills) <= 4

    def test_no_duplicate_skills(self):
        """Skill tags are unique even if keywords overlap."""
        skills = CourseService._extract_skills_from_title(
            "Data and data analytics"
        )
        assert skills.count("Data") == 1


class TestApplyFilters:
    """Tests for CourseService._apply_filters."""

    def _make_courses(self):
        return [
            Course("A", "P", "10 hours", "Part-time", 4.0, 50, 500, 100,
                   "80%", "High Impact", ["X"], "English"),
            Course("B", "P", "20 hours", "Full-time", 3.5, 30, 300, 60,
                   "80%", "Low Impact", ["Y"], "Mandarin"),
            Course("C", "P", "15 hours", "Part-time", 4.5, 40, 400, 80,
                   "80%", "High Impact", ["Z"], "English"),
        ]

    def test_no_filters_returns_all(self):
        """None filters return the original list unchanged."""
        courses = self._make_courses()
        result = CourseService._apply_filters(courses, None)
        assert len(result) == 3

    def test_empty_dict_returns_all(self):
        """An empty filter dict returns the original list."""
        courses = self._make_courses()
        result = CourseService._apply_filters(courses, {})
        assert len(result) == 3

    def test_filter_by_impact_level(self):
        """Impact filter keeps only matching courses."""
        courses = self._make_courses()
        result = CourseService._apply_filters(
            courses, {"impact_level": "High Impact"}
        )
        assert len(result) == 2
        assert all("High" in c.impact_level for c in result)

    def test_filter_by_mode(self):
        """Mode filter keeps only matching courses."""
        courses = self._make_courses()
        result = CourseService._apply_filters(
            courses, {"mode": "Full-time"}
        )
        assert len(result) == 1
        assert result[0].title == "B"

    def test_filter_by_language(self):
        """Language filter keeps only matching courses."""
        courses = self._make_courses()
        result = CourseService._apply_filters(
            courses, {"language": "Mandarin"}
        )
        assert len(result) == 1
        assert result[0].title == "B"

    def test_all_impact_levels_ignored(self):
        """'All Impact Levels' value does not restrict results."""
        courses = self._make_courses()
        result = CourseService._apply_filters(
            courses, {"impact_level": "All Impact Levels"}
        )
        assert len(result) == 3

    def test_all_modes_ignored(self):
        """'All Modes' value does not restrict results."""
        courses = self._make_courses()
        result = CourseService._apply_filters(
            courses, {"mode": "All Modes"}
        )
        assert len(result) == 3

    def test_all_languages_ignored(self):
        """'All Languages' value does not restrict results."""
        courses = self._make_courses()
        result = CourseService._apply_filters(
            courses, {"language": "All Languages"}
        )
        assert len(result) == 3

    def test_sort_by_highest_rating(self):
        """Sorting by rating orders highest first."""
        courses = self._make_courses()
        result = CourseService._apply_filters(
            courses, {"sort_by": "Highest Rating"}
        )
        assert result[0].title == "C"  # rating 4.5
        assert result[-1].title == "B"  # rating 3.5

    def test_sort_by_lowest_price(self):
        """Sorting by price orders lowest subsidised price first."""
        courses = self._make_courses()
        result = CourseService._apply_filters(
            courses, {"sort_by": "Lowest Price"}
        )
        assert result[0].title == "B"  # sub price 60

    def test_sort_by_shortest_duration(self):
        """Sorting by duration orders shortest first."""
        courses = self._make_courses()
        result = CourseService._apply_filters(
            courses, {"sort_by": "Shortest Duration"}
        )
        assert result[0].title == "A"  # 10 hours

    def test_combined_filter_and_sort(self):
        """Filters and sort can be applied together."""
        courses = self._make_courses()
        result = CourseService._apply_filters(courses, {
            "impact_level": "High Impact",
            "sort_by": "Highest Rating",
        })
        assert len(result) == 2
        assert result[0].title == "C"  # higher rating among High Impact


class TestParseHelpers:
    """Tests for the static field-parsing helpers."""

    def test_safe_int_valid(self):
        assert CourseService._safe_int("42", 0) == 42

    def test_safe_int_float_string(self):
        assert CourseService._safe_int("42.7", 0) == 42

    def test_safe_int_none(self):
        assert CourseService._safe_int(None, 99) == 99

    def test_safe_int_invalid(self):
        assert CourseService._safe_int("abc", 99) == 99

    def test_safe_int_string_none(self):
        assert CourseService._safe_int("None", 99) == 99

    def test_safe_str_valid(self):
        assert CourseService._safe_str("  hello  ", "default") == "hello"

    def test_safe_str_none(self):
        assert CourseService._safe_str(None, "default") == "default"

    def test_safe_str_string_none(self):
        assert CourseService._safe_str("None", "default") == "default"

    def test_clean_text_strips_carriage(self):
        result = CourseService._clean_text("line1_x000D_line2")
        assert "_x000D_" not in result

    def test_clean_text_none(self):
        assert CourseService._clean_text(None) is None

    def test_parse_duration_valid(self):
        assert CourseService._parse_duration("40") == "40 hours"

    def test_parse_duration_zero(self):
        assert CourseService._parse_duration("0") == "N/A"

    def test_parse_duration_none(self):
        assert CourseService._parse_duration(None) == "N/A"

    def test_parse_rating_valid(self):
        assert CourseService._parse_rating("4.5") == 4.5

    def test_parse_rating_clamped_high(self):
        assert CourseService._parse_rating("6.0") == 5.0

    def test_parse_rating_clamped_low(self):
        assert CourseService._parse_rating("0.2") == 1.0

    def test_parse_rating_none_gives_fallback(self):
        rating = CourseService._parse_rating(None)
        assert 4.3 <= rating <= 4.9

    def test_parse_reviews_valid(self):
        assert CourseService._parse_reviews("150") == 150

    def test_parse_reviews_none_gives_fallback(self):
        reviews = CourseService._parse_reviews(None)
        assert 100 <= reviews <= 2000

    def test_parse_impact_high(self):
        assert CourseService._parse_impact("4.5", 1000) == "High Impact"

    def test_parse_impact_medium(self):
        assert CourseService._parse_impact("3.5", 1000) == "Medium Impact"

    def test_parse_impact_low(self):
        assert CourseService._parse_impact("2.0", 1000) == "Low Impact"

    def test_parse_impact_zero_expensive(self):
        assert CourseService._parse_impact("0", 15000) == "High Impact"

    def test_parse_impact_zero_cheap(self):
        assert CourseService._parse_impact("0", 500) == "Medium Impact"

    def test_parse_impact_none_expensive(self):
        assert CourseService._parse_impact(None, 15000) == "High Impact"

    def test_parse_impact_none_cheap(self):
        assert CourseService._parse_impact(None, 500) == "Medium Impact"
