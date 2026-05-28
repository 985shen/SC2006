"""Service for loading and parsing industry / job-vacancy data.

Reads the Job Vacancies CSV (downloaded by :class:`DataDownloader`) and
converts it into a ranked list of :class:`Industry` objects.
"""

import csv
from typing import List, Tuple

from app.models.career import Industry
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

        Returns:
            Tuple of (success, list_of_Industry_objects, error_message).
        """
        success, csv_path = self.downloader.download_job_vacancies_csv()

        if not success:
            return False, [], "Error retrieving industries"

        industries: List[Industry] = []

        try:
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
                return True, industries[:10], ""
        except Exception:
            return False, [], "Error retrieving industries"
