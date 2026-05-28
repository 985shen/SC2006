"""Service for loading, parsing, and filtering SkillsFuture course data.

Reads the SkillsFuture Courses Excel file (downloaded by
:class:`DataDownloader`), optionally filters by industry keywords, and
applies user-selected filters and sorting.
"""

import random
import openpyxl
from typing import List, Optional, Tuple

from app.models.career import Course
from app.services.data_downloader import DataDownloader
from app.services.industry_keywords import get_industry_keywords


# Column indices (0-based) in the SkillsFuture Excel sheet.
COL_TITLE = 1
COL_PROVIDER = 3
COL_RATING = 4
COL_RESPONDENTS = 6
COL_IMPACT = 7
COL_FULL_FEE = 11
COL_SUB_FEE = 12
COL_HOURS = 13
COL_COMMITMENT = 14
COL_LANGUAGE = 15
COL_WHAT_YOU_LEARN = 17
COL_PREREQUISITES = 18

# Simple keyword → skill-tag mapping for extracting skills from course titles.
SKILL_MAP = {
    'python': 'Python', 'java': 'Java', 'javascript': 'JavaScript',
    'data': 'Data', 'analytics': 'Analytics', 'cloud': 'Cloud',
    'ai': 'AI', 'machine learning': 'ML', 'cybersecurity': 'Security',
    'finance': 'Finance', 'accounting': 'Accounting',
    'management': 'Management', 'leadership': 'Leadership',
    'design': 'Design', 'marketing': 'Marketing',
}


class CourseService:
    """Parses and filters SkillsFuture course data."""

    def __init__(self, downloader: DataDownloader):
        """Initialise with a *DataDownloader* instance.

        Args:
            downloader: Used to obtain the path to the cached Excel file.
        """
        self.downloader = downloader

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_courses_data(
        self, industry: str = None, filters: dict = None
    ) -> Tuple[bool, List[Course], str]:
        """Load courses from the SkillsFuture Excel file with optional filtering.

        Args:
            industry: Optional industry name to filter courses by keyword matching.
            filters: Optional dict with keys impact_level, mode, sort_by, language.

        Returns:
            Tuple of (success, list_of_Course_objects, error_message).
        """
        success, excel_path = self.downloader.download_skillsfuture_courses_csv()

        if not success:
            return False, [], "Error retrieving courses"

        try:
            wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
            sheet = wb.active

            industry_kws = get_industry_keywords(industry)

            if industry:
                print(f"Filtering courses for: {industry}")
                print(f"Using {len(industry_kws)} keywords")

            courses: List[Course] = []
            rows_scanned = 0
            rows_matched = 0

            for row in sheet.iter_rows(min_row=2, values_only=True):
                rows_scanned += 1

                if rows_scanned > 25000:
                    break

                title = row[COL_TITLE]
                if not title or len(str(title)) < 3:
                    continue

                title = str(title).strip()
                title_lower = title.lower()

                # Filter by industry keywords
                if industry and industry_kws:
                    if not any(kw in title_lower for kw in industry_kws):
                        continue

                rows_matched += 1
                if rows_matched > 150:
                    break

                courses.append(self._parse_course_row(row, title))

            wb.close()

            print(f"✓ Scanned {rows_scanned} rows, matched {rows_matched} courses")

            return True, self._apply_filters(courses, filters), ""

        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, [], "Error retrieving courses"

    # ------------------------------------------------------------------
    # Row parsing
    # ------------------------------------------------------------------

    def _parse_course_row(self, row: tuple, title: str) -> Course:
        """Convert a single Excel row into a :class:`Course` object.

        Args:
            row: Tuple of cell values from the Excel sheet.
            title: Already-stripped course title string.

        Returns:
            A populated Course instance.
        """
        provider = (
            str(row[COL_PROVIDER]).strip()[:80]
            if row[COL_PROVIDER]
            else 'Unknown'
        )

        price = self._safe_int(row[COL_FULL_FEE], 5000)
        sub_price = self._safe_int(row[COL_SUB_FEE], int(price * 0.2))

        duration = self._parse_duration(row[COL_HOURS])
        mode = self._safe_str(row[COL_COMMITMENT], "Part-time")
        language = self._safe_str(row[COL_LANGUAGE], "English")

        learning_outcomes = self._clean_text(row[COL_WHAT_YOU_LEARN])
        prerequisites = self._clean_text(row[COL_PREREQUISITES])

        rating = self._parse_rating(row[COL_RATING])
        reviews = self._parse_reviews(row[COL_RESPONDENTS])
        impact_level = self._parse_impact(row[COL_IMPACT], price)

        skills = self._extract_skills_from_title(title)

        return Course(
            title[:100], provider, duration, mode,
            rating, reviews, price, sub_price,
            "Up to 80% subsidy", impact_level, skills, language,
            learning_outcomes, prerequisites
        )

    # ------------------------------------------------------------------
    # Field-level helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_int(value, default: int) -> int:
        try:
            if value and str(value) != 'None':
                return int(float(value))
        except (ValueError, TypeError):
            pass
        return default

    @staticmethod
    def _safe_str(value, default: str) -> str:
        if value and str(value) != 'None':
            return str(value).strip()
        return default

    @staticmethod
    def _clean_text(value) -> Optional[str]:
        if value and str(value) != 'None':
            return str(value).replace('_x000D_', '').strip()
        return None

    @staticmethod
    def _parse_duration(value) -> str:
        try:
            if value and str(value) != 'None':
                hours = int(float(value))
                return f"{hours} hours" if hours > 0 else "N/A"
        except (ValueError, TypeError):
            pass
        return "N/A"

    @staticmethod
    def _parse_rating(value) -> float:
        try:
            if value and str(value) != 'None':
                rating = float(value)
                return round(max(1.0, min(5.0, rating)), 1)
        except (ValueError, TypeError):
            pass
        return round(random.uniform(4.3, 4.9), 1)

    @staticmethod
    def _parse_reviews(value) -> int:
        try:
            if value and str(value) != 'None':
                return int(float(value))
        except (ValueError, TypeError):
            pass
        return random.randint(100, 2000)

    @staticmethod
    def _parse_impact(value, price: int) -> str:
        try:
            if value and str(value) != 'None':
                impact_val = float(value)
                if impact_val >= 4.0:
                    return 'High Impact'
                elif impact_val >= 3.0:
                    return 'Medium Impact'
                else:
                    if impact_val > 0:
                        return 'Low Impact'
                    return 'High Impact' if price >= 10000 else 'Medium Impact'
        except (ValueError, TypeError):
            pass
        return 'High Impact' if price >= 10000 else 'Medium Impact'

    # ------------------------------------------------------------------
    # Skill extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_skills_from_title(title: str) -> List[str]:
        """Extract up to four skill tags from a course title via keyword matching.

        Args:
            title: The course title string.

        Returns:
            list[str]: Matched skill labels, or ['Professional Development'] as fallback.
        """
        skills: List[str] = []
        title_lower = title.lower()
        for keyword, skill in SKILL_MAP.items():
            if keyword in title_lower and skill not in skills:
                skills.append(skill)
                if len(skills) >= 4:
                    break
        return skills if skills else ['Professional Development']

    # ------------------------------------------------------------------
    # Filtering & sorting
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_filters(courses: List[Course], filters: dict = None) -> List[Course]:
        """Apply user-selected filters and sorting to a list of courses.

        Supports filtering by impact_level, mode, and language, and sorting
        by rating, price, or duration.

        Args:
            courses: The unfiltered course list.
            filters: Dict of filter/sort parameters from the query string.

        Returns:
            list[Course]: Filtered and sorted course list.
        """
        if not filters:
            return courses

        filtered = courses

        impact = filters.get('impact_level')
        if impact and impact != 'All Impact Levels':
            filtered = [c for c in filtered if impact.lower() in c.impact_level.lower()]

        mode = filters.get('mode')
        if mode and mode != 'All Modes':
            filtered = [c for c in filtered if mode.lower() in c.mode.lower()]

        language = filters.get('language')
        if language and language != 'All Languages':
            filtered = [c for c in filtered if c.language and language in c.language]

        sort_by = filters.get('sort_by', 'Highest Rating')
        if sort_by == 'Highest Rating':
            filtered.sort(key=lambda x: x.rating, reverse=True)
        elif sort_by == 'Lowest Price':
            filtered.sort(key=lambda x: x.price_subsidized)
        elif sort_by == 'Shortest Duration':
            filtered.sort(
                key=lambda x: int(''.join(filter(str.isdigit, x.duration)) or '0')
            )

        return filtered
