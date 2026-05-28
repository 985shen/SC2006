"""Download and cache data files from the Singapore Government open-data APIs.

Provides methods to fetch the Job Vacancies CSV and the SkillsFuture
Courses Excel file, storing them locally under the ``CSV/`` directory
and skipping re-download when the cached copy is still fresh.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Tuple


class DataDownloader:
    """Manages downloading and caching of government dataset files."""

    def __init__(self, jobs_api_url: str, courses_api_url: str,
                 csv_dir: str = 'CSV', timeout: int = 60):
        """Initialise the downloader.

        Args:
            jobs_api_url: Endpoint URL for the job vacancies dataset.
            courses_api_url: Endpoint URL for the SkillsFuture courses dataset.
            csv_dir: Local directory to cache downloaded files.
            timeout: HTTP request timeout in seconds.
        """
        self.jobs_api_url = jobs_api_url
        self.courses_api_url = courses_api_url
        self.csv_dir = csv_dir
        self.timeout = timeout
        self._ensure_csv_directory_exists()

    def _ensure_csv_directory_exists(self):
        """Create the local CSV cache directory if it does not already exist."""
        if not os.path.exists(self.csv_dir):
            os.makedirs(self.csv_dir)

    def _should_refresh(self, filepath: str, max_age_hours: int = 24) -> bool:
        """Determine whether a cached file should be re-downloaded.

        Args:
            filepath: Path to the cached file on disk.
            max_age_hours: Maximum age in hours before the file is considered stale.

        Returns:
            bool: True if the file is missing or older than *max_age_hours*.
        """
        if not os.path.exists(filepath):
            return True
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(filepath))
        return file_age > timedelta(hours=max_age_hours)

    def _download_from_data_gov(self, dataset_id: str, filepath: str) -> Tuple[bool, str]:
        """Generic helper to poll and download a dataset from data.gov.sg.

        Args:
            dataset_id: The data.gov.sg dataset identifier.
            filepath: Local path to save the downloaded file.

        Returns:
            Tuple of (success, filepath_or_error_message).
        """
        try:
            poll_url = (
                f"https://api-open.data.gov.sg/v1/public/api/datasets/"
                f"{dataset_id}/poll-download"
            )

            response = requests.get(poll_url, timeout=self.timeout)
            json_data = response.json()

            if json_data.get('code') != 0:
                return False, json_data.get('errMsg', 'Unknown error')

            download_url = json_data['data']['url']
            download_response = requests.get(
                download_url, stream=True, timeout=self.timeout
            )

            if download_response.status_code == 200:
                with open(filepath, 'wb') as file:
                    for chunk in download_response.iter_content(chunk_size=8192):
                        file.write(chunk)
                return True, filepath
            return False, "Download failed"
        except Exception as e:
            # Fall back to existing cache if available
            if os.path.exists(filepath):
                return True, filepath
            return False, str(e)

    def download_job_vacancies_csv(self) -> Tuple[bool, str]:
        """Download the Job Vacancies CSV from data.gov.sg if the cache is stale.

        Returns:
            Tuple of (success, filepath_or_error_message).
        """
        csv_filepath = os.path.join(self.csv_dir, 'JobVacancies.csv')

        if not self._should_refresh(csv_filepath):
            return True, csv_filepath

        dataset_id = "d_f3bbdfbf92b811fff364aeed23b5e0bb"
        return self._download_from_data_gov(dataset_id, csv_filepath)

    def download_skillsfuture_courses_csv(self) -> Tuple[bool, str]:
        """Download the SkillsFuture Courses Excel file from data.gov.sg if stale.

        Returns:
            Tuple of (success, filepath_or_error_message).
        """
        excel_filepath = os.path.join(self.csv_dir, 'SkillsFutureCourses.xlsx')

        if not self._should_refresh(excel_filepath):
            return True, excel_filepath

        dataset_id = "d_b5802b76f409764c16dde4bf2feb19cd"
        return self._download_from_data_gov(dataset_id, excel_filepath)
