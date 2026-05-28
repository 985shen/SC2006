"""Basis Path Tests for score_specifics and _apply_filters.

Two methods are tested using McCabe's basis path testing technique:

    1. RuleBasedScorer.score_specifics(text)
       - Cyclomatic complexity V(G) = 6
       - 6 linearly independent paths

    2. CourseService._apply_filters(courses, filters)
       - Cyclomatic complexity V(G) = 9
       - 9 linearly independent paths

Each test is explicitly mapped to a path through the Control Flow Graph (CFG).
Together, the paths in each group guarantee full edge coverage of the CFG.
"""

import pytest
from app.models.career import Course
from app.services.resume_grading_service import RuleBasedScorer
from app.services.course_service import CourseService


# ──────────────────────────────────────────────────────────────────────
# Helper: build a list of Course objects for _apply_filters tests
# ──────────────────────────────────────────────────────────────────────

def _make_courses():
    """Return a fixed set of 4 courses with varied attributes for filtering."""
    return [
        Course("Python Bootcamp", "ProvA", "10 hours", "Part-time",
               4.5, 50, 500, 100, "80%", "High Impact", ["Python"], "English"),
        Course("Java Masterclass", "ProvB", "30 hours", "Full-time",
               3.0, 30, 300, 60, "80%", "Low Impact", ["Java"], "Mandarin"),
        Course("Cloud Fundamentals", "ProvC", "20 hours", "Part-time",
               4.0, 40, 400, 80, "80%", "High Impact", ["Cloud"], "English"),
        Course("Design Thinking", "ProvD", "15 hours", "Full-time",
               3.5, 20, 600, 200, "67%", "Medium Impact", ["Design"], "English"),
    ]


# ══════════════════════════════════════════════════════════════════════
#  METHOD 1 — RuleBasedScorer.score_specifics(text)
# ══════════════════════════════════════════════════════════════════════
#
#  CFG nodes:
#    N1  – entry
#    N2  – bullets = _bullet_lines(text) or _sentences(text); if not bullets?
#    N3  – return {points: 0}  (bullets empty)
#    N4  – compute ratio = quantified / len(bullets); if ratio >= 0.6?
#    N5  – pts = 8
#    N6  – if ratio >= 0.4?
#    N7  – pts = 6
#    N8  – if ratio >= 0.2?
#    N9  – pts = 4
#    N10 – if quantified > 0?
#    N11 – pts = 2
#    N12 – pts = 0
#    N13 – return result
#
#  V(G) = 6  (5 predicate nodes + 1)
#  Independent paths:
#    Path 1: N1 → N2(T)  → N3  → N13          bullets empty
#    Path 2: N1 → N2(F)  → N4(T) → N5 → N13   ratio >= 0.6
#    Path 3: N1 → N2(F)  → N4(F) → N6(T) → N7 → N13   0.4 <= ratio < 0.6
#    Path 4: N1 → N2(F)  → N4(F) → N6(F) → N8(T) → N9 → N13   0.2 <= ratio < 0.4
#    Path 5: N1 → N2(F)  → N4(F) → N6(F) → N8(F) → N10(T) → N11 → N13  ratio < 0.2, quantified > 0
#    Path 6: N1 → N2(F)  → N4(F) → N6(F) → N8(F) → N10(F) → N12 → N13  quantified == 0
# ══════════════════════════════════════════════════════════════════════


class TestScoreSpecificsBasisPaths:
    """Basis path tests for RuleBasedScorer.score_specifics.

    Each test exercises exactly one independent path through the CFG.
    """

    def test_path1_no_bullets_no_sentences(self):
        """Path 1: N1 → N2(True) → N3 → N13

        Text has no bullet lines AND no sentence-ending punctuation,
        so _bullet_lines returns [] and _sentences returns [].
        The guard `if not bullets` is True → early return with pts=0.
        """
        text = ""  # empty string produces no bullets and no sentences
        result = RuleBasedScorer.score_specifics(text)

        assert result["points"] == 0
        assert result["quantified"] == 0
        assert result["total"] == 0

    def test_path2_ratio_gte_060(self):
        """Path 2: N1 → N2(False) → N4(True) → N5 → N13

        Supply 5 bullet lines, 4 of which contain numbers.
        ratio = 4/5 = 0.80 ≥ 0.6 → pts = 8.
        """
        text = (
            "• Increased revenue by 30%\n"
            "• Managed team of 12 engineers\n"
            "• Reduced costs by 15%\n"
            "• Deployed 3 microservices\n"
            "• Led the design initiative\n"  # no number
        )
        result = RuleBasedScorer.score_specifics(text)

        assert result["points"] == 8
        assert result["quantified"] == 4
        assert result["total"] == 5

    def test_path3_ratio_gte_040_lt_060(self):
        """Path 3: N1 → N2(F) → N4(F) → N6(True) → N7 → N13

        Supply 5 bullet lines, 2 with numbers.
        ratio = 2/5 = 0.40 → exactly on the 0.4 boundary → pts = 6.
        """
        text = (
            "• Increased revenue by 30%\n"
            "• Managed team of 12 engineers\n"
            "• Led the design initiative\n"
            "• Coordinated cross-team efforts\n"
            "• Improved onboarding process\n"
        )
        result = RuleBasedScorer.score_specifics(text)

        assert result["points"] == 6
        assert result["quantified"] == 2
        assert result["total"] == 5

    def test_path4_ratio_gte_020_lt_040(self):
        """Path 4: N1 → N2(F) → N4(F) → N6(F) → N8(True) → N9 → N13

        Supply 5 bullet lines, 1 with a number.
        ratio = 1/5 = 0.20 → exactly on the 0.2 boundary → pts = 4.
        """
        text = (
            "• Increased revenue by 30%\n"
            "• Led the design initiative\n"
            "• Coordinated cross-team efforts\n"
            "• Improved onboarding process\n"
            "• Streamlined workflows\n"
        )
        result = RuleBasedScorer.score_specifics(text)

        assert result["points"] == 4
        assert result["quantified"] == 1
        assert result["total"] == 5

    def test_path5_ratio_lt_020_quantified_gt_0(self):
        """Path 5: N1 → N2(F) → N4(F) → N6(F) → N8(F) → N10(True) → N11 → N13

        Supply 6 bullet lines, 1 with a number.
        ratio = 1/6 ≈ 0.167 < 0.2, but quantified = 1 > 0 → pts = 2.
        """
        text = (
            "• Increased revenue by 30%\n"
            "• Led the design initiative\n"
            "• Coordinated cross-team efforts\n"
            "• Improved onboarding process\n"
            "• Streamlined internal workflows\n"
            "• Enhanced team communication\n"
        )
        result = RuleBasedScorer.score_specifics(text)

        assert result["points"] == 2
        assert result["quantified"] == 1
        assert result["total"] == 6

    def test_path6_quantified_zero(self):
        """Path 6: N1 → N2(F) → N4(F) → N6(F) → N8(F) → N10(False) → N12 → N13

        Supply bullet lines with NO numbers at all.
        quantified = 0, ratio = 0.0 → falls through every branch → pts = 0.
        """
        text = (
            "• Led the design initiative\n"
            "• Coordinated cross-team efforts\n"
            "• Improved onboarding process\n"
        )
        result = RuleBasedScorer.score_specifics(text)

        assert result["points"] == 0
        assert result["quantified"] == 0
        assert result["total"] == 3


# ══════════════════════════════════════════════════════════════════════
#  METHOD 2 — CourseService._apply_filters(courses, filters)
# ══════════════════════════════════════════════════════════════════════
#
#  CFG nodes:
#    N1  – entry
#    N2  – if not filters? → return courses
#    N3  – impact = filters.get('impact_level'); if impact and impact != 'All ...'?
#    N4  – filter by impact
#    N5  – mode = filters.get('mode'); if mode and mode != 'All Modes'?
#    N6  – filter by mode
#    N7  – language = filters.get('language'); if language and language != 'All ...'?
#    N8  – filter by language
#    N9  – sort_by = filters.get('sort_by', 'Highest Rating')
#    N10 – if sort_by == 'Highest Rating'?  → sort descending by rating
#    N11 – elif sort_by == 'Lowest Price'?  → sort ascending by price_subsidized
#    N12 – elif sort_by == 'Shortest Duration'? → sort ascending by duration digits
#    N13 – (else: no sort applied)
#    N14 – return filtered
#
#  Decision points:
#    D1: not filters                          (N2)
#    D2: impact truthy                        (N3, part 1)
#    D3: impact != 'All Impact Levels'        (N3, part 2)
#    D4: mode truthy                          (N5, part 1)
#    D5: mode != 'All Modes'                  (N5, part 2)
#    D6: language truthy                      (N7, part 1)
#    D7: language != 'All Languages'          (N7, part 2)
#    D8: sort_by == 'Highest Rating'          (N10)
#    D9: sort_by == 'Lowest Price'            (N11)
#    (D10: sort_by == 'Shortest Duration' is reached only when D8=F, D9=F)
#
#  V(G) = 9   (8 binary decisions + 1)
#  Independent paths — each flips exactly one new edge:
#
#    Path 1: filters=None → return all                  (D1=T)
#    Path 2: filters={}, sort default → sort by rating  (D1=F, D2=F, D4=F, D6=F, D8=T)
#    Path 3: impact="High Impact" applied               (D1=F, D2=T, D3=T)
#    Path 4: impact="All Impact Levels" skipped         (D1=F, D2=T, D3=F)
#    Path 5: mode="Full-time" applied                   (D1=F, D4=T, D5=T)
#    Path 6: mode="All Modes" skipped                   (D1=F, D4=T, D5=F)
#    Path 7: language="Mandarin" applied                (D1=F, D6=T, D7=T)
#    Path 8: sort_by="Lowest Price"                     (D1=F, D8=F, D9=T)
#    Path 9: sort_by="Shortest Duration"                (D1=F, D8=F, D9=F, D10=T)
# ══════════════════════════════════════════════════════════════════════


class TestApplyFiltersBasisPaths:
    """Basis path tests for CourseService._apply_filters.

    Each test exercises exactly one independent path through the CFG.
    """

    def test_path1_filters_none(self):
        """Path 1: N1 → N2(True) → return courses

        filters is None → guard clause fires, original list returned unchanged.
        (An empty dict {} also triggers this path since `not {}` is True.)
        """
        courses = _make_courses()
        result = CourseService._apply_filters(courses, None)

        assert len(result) == 4
        assert result is courses  # same object — no copy

    def test_path2_no_matching_filters_default_sort(self):
        """Path 2: N1 → N2(F) → N3(skip) → N5(skip) → N7(skip) → N10(T) → N14

        Dict with sort_by='Highest Rating' only (no filter keys).
        All filter guards (D2,D4,D6) are False because keys absent.
        sort_by == 'Highest Rating' → D8=True → sort descending by rating.

        Note: an empty dict {} would trigger `not filters` = True (Path 1),
        so we must supply at least one key to reach the filter/sort logic.
        """
        courses = _make_courses()
        result = CourseService._apply_filters(
            courses, {"sort_by": "Highest Rating"}
        )

        assert len(result) == 4
        # Verify descending rating order
        assert result[0].rating == 4.5  # Python Bootcamp
        assert result[1].rating == 4.0  # Cloud Fundamentals
        assert result[2].rating == 3.5  # Design Thinking
        assert result[3].rating == 3.0  # Java Masterclass

    def test_path3_impact_filter_applied(self):
        """Path 3: N1 → N2(F) → N3(T, impact truthy) → N4(T, != 'All') → … → N14

        impact_level='High Impact' — only courses with 'High Impact' survive.
        D2=True, D3=True → filter list comprehension executes.
        """
        courses = _make_courses()
        result = CourseService._apply_filters(
            courses, {"impact_level": "High Impact"}
        )

        assert len(result) == 2
        assert all("High" in c.impact_level for c in result)
        titles = {c.title for c in result}
        assert "Python Bootcamp" in titles
        assert "Cloud Fundamentals" in titles

    def test_path4_impact_all_levels_skipped(self):
        """Path 4: N1 → N2(F) → N3(T, impact truthy) → N4(F, == 'All') → … → N14

        impact_level='All Impact Levels' — D2=True but D3=False,
        so the filter comprehension is skipped and all courses survive.
        """
        courses = _make_courses()
        result = CourseService._apply_filters(
            courses, {"impact_level": "All Impact Levels"}
        )

        assert len(result) == 4

    def test_path5_mode_filter_applied(self):
        """Path 5: N1 → N2(F) → … → N5(T, mode truthy) → N6(T, != 'All') → … → N14

        mode='Full-time' — only full-time courses survive.
        D4=True, D5=True → filter applied.
        """
        courses = _make_courses()
        result = CourseService._apply_filters(
            courses, {"mode": "Full-time"}
        )

        assert len(result) == 2
        assert all("Full-time" in c.mode for c in result)
        titles = {c.title for c in result}
        assert "Java Masterclass" in titles
        assert "Design Thinking" in titles

    def test_path6_mode_all_modes_skipped(self):
        """Path 6: N1 → N2(F) → … → N5(T, mode truthy) → N6(F, == 'All') → … → N14

        mode='All Modes' — D4=True but D5=False,
        so the mode filter is skipped.
        """
        courses = _make_courses()
        result = CourseService._apply_filters(
            courses, {"mode": "All Modes"}
        )

        assert len(result) == 4

    def test_path7_language_filter_applied(self):
        """Path 7: N1 → N2(F) → … → N7(T, lang truthy) → N8(T, != 'All') → … → N14

        language='Mandarin' — only Mandarin courses survive.
        D6=True, D7=True → filter applied.
        """
        courses = _make_courses()
        result = CourseService._apply_filters(
            courses, {"language": "Mandarin"}
        )

        assert len(result) == 1
        assert result[0].title == "Java Masterclass"
        assert result[0].language == "Mandarin"

    def test_path8_sort_by_lowest_price(self):
        """Path 8: N1 → N2(F) → … → N10(F) → N11(T, 'Lowest Price') → N14

        sort_by='Lowest Price' — D8=False, D9=True.
        Courses sorted ascending by price_subsidized.
        """
        courses = _make_courses()
        result = CourseService._apply_filters(
            courses, {"sort_by": "Lowest Price"}
        )

        assert len(result) == 4
        prices = [c.price_subsidized for c in result]
        assert prices == sorted(prices)
        assert result[0].title == "Java Masterclass"   # sub price 60
        assert result[-1].title == "Design Thinking"    # sub price 200

    def test_path9_sort_by_shortest_duration(self):
        """Path 9: N1 → N2(F) → … → N10(F) → N11(F) → N12(T, 'Shortest Duration') → N14

        sort_by='Shortest Duration' — D8=False, D9=False, D10=True.
        Courses sorted ascending by numeric hours extracted from duration string.
        """
        courses = _make_courses()
        result = CourseService._apply_filters(
            courses, {"sort_by": "Shortest Duration"}
        )

        assert len(result) == 4
        assert result[0].title == "Python Bootcamp"    # 10 hours
        assert result[1].title == "Design Thinking"     # 15 hours
        assert result[2].title == "Cloud Fundamentals"  # 20 hours
        assert result[3].title == "Java Masterclass"    # 30 hours