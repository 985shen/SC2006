"""Facade that composes the specialised data services.

This module preserves the original :class:`DataService` public interface so
that controllers and tests can continue to import and use it unchanged.
Internally it delegates to :class:`DataDownloader`, :class:`IndustryService`,
and :class:`CourseService`.
"""

from typing import List, Tuple

from app.models.career import Industry, Course, DashboardStats
from app.services.data_downloader import DataDownloader
from app.services.industry_service import IndustryService
from app.services.course_service import CourseService
from app.services.industry_keywords import get_industry_keywords


class DataService:
    """Service to fetch and process data from Singapore Government APIs.

    Acts as a backward-compatible facade over the smaller, focused
    service classes that were extracted from the original monolith.
    """

    def __init__(self, jobs_api_url: str, courses_api_url: str):
        """Initialise the DataService with API URLs.

        Args:
            jobs_api_url: Endpoint URL for the Singapore job vacancies dataset.
            courses_api_url: Endpoint URL for the SkillsFuture courses dataset.
        """
        self._downloader = DataDownloader(
            jobs_api_url=jobs_api_url,
            courses_api_url=courses_api_url,
        )
        self._industry_service = IndustryService(self._downloader)
        self._course_service = CourseService(self._downloader)

        # Expose the keyword registry so existing tests that access
        # ``service.industry_keywords`` or ``service._get_industry_keywords``
        # keep working.
        from app.services.industry_keywords import INDUSTRY_KEYWORDS
        self.industry_keywords = INDUSTRY_KEYWORDS

    # ------------------------------------------------------------------
    # Delegated download helpers (kept for any direct callers)
    # ------------------------------------------------------------------

    def download_job_vacancies_csv(self) -> Tuple[bool, str]:
        """Download the Job Vacancies CSV from data.gov.sg if the cache is stale."""
        return self._downloader.download_job_vacancies_csv()

    def download_skillsfuture_courses_csv(self) -> Tuple[bool, str]:
        """Download the SkillsFuture Courses Excel file from data.gov.sg if stale."""
        return self._downloader.download_skillsfuture_courses_csv()

    # ------------------------------------------------------------------
    # Delegated data retrieval
    # ------------------------------------------------------------------

    def get_industries_data(self) -> Tuple[bool, List[Industry], str]:
        """Load and parse industry data from the Job Vacancies CSV."""
        return self._industry_service.get_industries_data()

    def get_courses_data(
        self, industry: str = None, filters: dict = None
    ) -> Tuple[bool, List[Course], str]:
        """Load courses from the SkillsFuture Excel file with optional filtering."""
        return self._course_service.get_courses_data(industry=industry, filters=filters)

    # ------------------------------------------------------------------
    # Delegated helpers (preserved for backward compatibility with tests)
    # ------------------------------------------------------------------

    @staticmethod
    def _get_industry_keywords(industry: str) -> list:
        """Retrieve the keyword list associated with a given industry name."""
        return get_industry_keywords(industry)

    @staticmethod
    def _extract_skills_from_title(title: str) -> List[str]:
        """Extract up to four skill tags from a course title."""
        return CourseService._extract_skills_from_title(title)

    @staticmethod
    def _apply_filters(courses: List[Course], filters: dict = None) -> List[Course]:
        """Apply user-selected filters and sorting to a list of courses."""
        return CourseService._apply_filters(courses, filters)

    # ------------------------------------------------------------------
    # Dashboard statistics
    # ------------------------------------------------------------------

    def get_dashboard_stats(self) -> DashboardStats:
        """Compute aggregate statistics for the public dashboard.

        Returns:
            DashboardStats with total vacancies, industry count, and course count.
        """
        success, industries, _ = self.get_industries_data()
        success_courses, all_courses, _ = self.get_courses_data()

        total_vacancies = sum(ind.vacancies for ind in industries) if industries else 72110
        top_industries = len(industries) if industries else 10
        total_courses = len(all_courses) if all_courses else 150

        return DashboardStats(total_vacancies, top_industries, total_courses)
