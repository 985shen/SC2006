"""Unit tests for the career dataclass models (Industry, Course, DashboardStats)."""

import pytest
from app.models.career import Industry, Course, DashboardStats


class TestIndustryModel:
    """Tests for the Industry dataclass."""

    def test_positive_growth_display(self):
        """Positive growth shows a '+' prefix."""
        ind = Industry("IT", 5000, 12.5, "💻")
        assert ind.get_growth_display() == "+12.5%"

    def test_negative_growth_display(self):
        """Negative growth shows a '-' prefix."""
        ind = Industry("Retail", 2000, -3.2, "🛒")
        assert ind.get_growth_display() == "-3.2%"

    def test_zero_growth_display(self):
        """Zero growth shows a '+' prefix."""
        ind = Industry("Finance", 3000, 0.0, "💰")
        assert ind.get_growth_display() == "+0.0%"


class TestCourseModel:
    """Tests for the Course dataclass."""

    def test_auto_generated_course_id(self):
        """course_id is auto-generated when not provided."""
        course = Course(
            title="Python 101", provider="SkillsFuture",
            duration="40 hours", mode="Part-time",
            rating=4.5, reviews=100,
            price_original=1000, price_subsidized=200,
            subsidy_text="80% off", impact_level="High Impact",
            skills=["Python"]
        )
        assert course.course_id is not None
        assert len(course.course_id) == 12

    def test_same_inputs_produce_same_id(self):
        """Same title+provider always produces the same course_id."""
        c1 = Course("Python 101", "SkillsFuture", "40h", "PT", 4.5, 100,
                     1000, 200, "80%", "High", ["Python"])
        c2 = Course("Python 101", "SkillsFuture", "20h", "FT", 3.0, 50,
                     500, 100, "50%", "Low", ["Coding"])
        assert c1.course_id == c2.course_id

    def test_different_inputs_produce_different_id(self):
        """Different title+provider produces a different course_id."""
        c1 = Course("Python 101", "Provider A", "40h", "PT", 4.5, 100,
                     1000, 200, "80%", "High", ["Python"])
        c2 = Course("Java 201", "Provider B", "40h", "PT", 4.5, 100,
                     1000, 200, "80%", "High", ["Java"])
        assert c1.course_id != c2.course_id

    def test_explicit_course_id_preserved(self):
        """An explicitly provided course_id is not overwritten."""
        course = Course("Test", "Provider", "10h", "PT", 4.0, 50,
                        500, 100, "80%", "Medium", ["Test"],
                        course_id="my_custom_id")
        assert course.course_id == "my_custom_id"

    def test_subsidy_percentage_normal(self):
        """Subsidy percentage is calculated correctly."""
        course = Course("Test", "Provider", "10h", "PT", 4.0, 50,
                        1000, 200, "80%", "High", ["Test"])
        assert course.get_subsidy_percentage() == 80

    def test_subsidy_percentage_no_discount(self):
        """Zero discount returns 0%."""
        course = Course("Test", "Provider", "10h", "PT", 4.0, 50,
                        1000, 1000, "0%", "Low", ["Test"])
        assert course.get_subsidy_percentage() == 0

    def test_subsidy_percentage_free(self):
        """Full subsidy returns 100%."""
        course = Course("Test", "Provider", "10h", "PT", 4.0, 50,
                        1000, 0, "Free", "High", ["Test"])
        assert course.get_subsidy_percentage() == 100

    def test_subsidy_percentage_zero_original(self):
        """Zero original price returns 0% (avoids division by zero)."""
        course = Course("Test", "Provider", "10h", "PT", 4.0, 50,
                        0, 0, "Free", "High", ["Test"])
        assert course.get_subsidy_percentage() == 0


class TestDashboardStats:
    """Tests for the DashboardStats dataclass."""

    def test_creation(self):
        """DashboardStats stores all fields."""
        stats = DashboardStats(total_vacancies=72000, top_industries=10, total_courses=150)
        assert stats.total_vacancies == 72000
        assert stats.top_industries == 10
        assert stats.total_courses == 150
