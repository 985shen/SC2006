"""Service for loading and parsing industry / job-vacancy data.

Reads the Job Vacancies CSV (downloaded by :class:`DataDownloader`) and
converts it into a ranked list of :class:`Industry` objects.

The parsed list is cached in memory via :mod:`app.services._cache` and
re-built only when the underlying CSV's mtime changes — typically once
per 24-hour download cycle.
"""

import csv
from typing import List, Tuple

from app.models.career import Industry
from app.services._cache import PARSED_FILE_CACHE
from app.services.data_downloader import DataDownloader


# Emoji icons keyed by substrings that may appear in an industry name.
ICON_MAP = {
    'information technology': '💻', 'infocomm': '💻',
    'healthcare': '🏥', 'medical': '🏥',
    'financial': '💰', 'finance': '💰',
    'engineering': '⚙️',
    'logistics': '📦', 'transport': '📦',
    'sales': '📊', 'marketing': '📊',
    'retail': '🛒',
    'education': '📚',
    'hospitality': '🏨', 'tourism': '🏨', 'food': '🍽️',
    'manufacturing': '🏭',
    'construction': '🏗️',
    'creative': '🎨', 'design': '🎨',
}


class IndustryService:
    """Parses industry data from the cached Job Vacancies CSV."""

    def __init__(self, downloader: DataDownloader):
        """Initialise with a *DataDownloader* instance.

        Args:
            downloader: Used to obtain the path to the cached CSV file.
        """
        self.downloader = downloader

    def get_industries_data(self) -> Tuple[bool, List[Industry], str]:
        """Load and parse industry data from the Job Vacancies CSV.

        Industries with fewer than 1000 vacancies are filtered out and the
        result is sorted by vacancy count descending, returning the top 10.

        The parsed result is cached; repeated calls within the cache window
        return the same list object without re-reading the CSV.

        Returns:
            Tuple of (success, list_of_Industry_objects, error_message).
        """
        success, csv_path = self.downloader.download_job_vacancies_csv()

        if not success:
            return False, [], "Error retrieving industries"

        try:
            industries = PARSED_FILE_CACHE.get_or_load(
                csv_path, self._parse_industries_csv, extra_key="industries"
            )
            return True, industries, ""
        except Exception:
            return False, [], "Error retrieving industries"

    @staticmethod
    def _parse_industries_csv(csv_path: str) -> List[Industry]:
        """Parse the Job Vacancies CSV into a top-10 list of Industry objects.

        Run once per refresh, then memoised by :data:`PARSED_FILE_CACHE`.
        """
        industries: List[Industry] = []

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header

            for row in reader:
                if not row or len(row) < 2:
                    continue

                industry_name = row[0].strip()
                if not industry_name or industry_name.lower() == 'total':
                    continue

                try:
                    vacancies = int(row[1]) if row[1] and row[1] != 'na' else 0
                    if vacancies < 1000:
                        continue

                    prev_vacancies = (
                        int(row[2])
                        if len(row) > 2 and row[2] and row[2] != 'na'
                        else vacancies
                    )
                    growth_rate = (
                        ((vacancies - prev_vacancies) / prev_vacancies * 100)
                        if prev_vacancies > 0
                        else 0.0
                    )
                except Exception:
                    continue

                icon = '💼'
                for keyword, emoji in ICON_MAP.items():
                    if keyword in industry_name.lower():
                        icon = emoji
                        break

                industries.append(
                    Industry(industry_name, vacancies, round(growth_rate, 1), icon)
                )

        industries.sort(key=lambda x: x.vacancies, reverse=True)
        return industries[:10]
