"""Download and cache data files from the Singapore Government open-data APIs.

Provides methods to fetch the Job Vacancies CSV and the SkillsFuture
Courses Excel file, storing them locally under the ``CSV/`` directory
and skipping re-download when the cached copy is still fresh.

The SkillsFuture dataset arrives as ``.xlsx``. Parsing xlsx with openpyxl
is markedly slower than reading a plain CSV, especially on Windows where
the per-file overhead and antivirus scans of zip-format documents dominate.
To work around that, the downloader transparently converts the xlsx to a
CSV alongside it on first download and exposes the CSV path to callers.
"""

import csv
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

        After a successful download the workbook is converted to a CSV
        (``SkillsFutureCourses.csv``) alongside the xlsx. Subsequent reads
        of the CSV are an order of magnitude faster than parsing xlsx with
        openpyxl — particularly on Windows. The path returned points at the
        CSV when conversion succeeds, otherwise the original xlsx (so the
        CourseService can still fall back to openpyxl).

        Returns:
            Tuple of (success, filepath_or_error_message). The filepath is
            a ``.csv`` when conversion succeeded, ``.xlsx`` otherwise.
        """
        excel_filepath = os.path.join(self.csv_dir, 'SkillsFutureCourses.xlsx')
        csv_filepath = os.path.join(self.csv_dir, 'SkillsFutureCourses.csv')

        # Fast path: a fresh CSV already exists from a previous run.
        if not self._should_refresh(csv_filepath) and os.path.exists(csv_filepath):
            return True, csv_filepath

        # Otherwise (re)download the xlsx, then convert to CSV.
        if self._should_refresh(excel_filepath):
            dataset_id = "d_b5802b76f409764c16dde4bf2feb19cd"
            ok, result = self._download_from_data_gov(dataset_id, excel_filepath)
            if not ok:
                # Download failed; fall back to whatever cached copy exists.
                if os.path.exists(csv_filepath):
                    return True, csv_filepath
                if os.path.exists(excel_filepath):
                    return True, excel_filepath
                return False, result

        # Convert xlsx -> csv once, then point callers at the CSV.
        if self._convert_xlsx_to_csv(excel_filepath, csv_filepath):
            return True, csv_filepath

        # Conversion failed for some reason; serve the xlsx so the caller
        # can still parse it via openpyxl.
        return True, excel_filepath

    @staticmethod
    def _convert_xlsx_to_csv(xlsx_path: str, csv_path: str) -> bool:
        """Convert the SkillsFuture xlsx workbook to a CSV beside it.

        Uses ``openpyxl`` in read-only mode so the conversion itself is
        memory-light. Done once per download cycle (every 24h by default),
        so the cost is amortised over thousands of subsequent reads.

        Args:
            xlsx_path: Source xlsx file.
            csv_path: Destination CSV path; overwritten if it already exists.

        Returns:
            True on success, False if openpyxl raises (in which case
            callers should fall back to reading the xlsx directly).
        """
        try:
            import openpyxl  # local import: only needed during conversion

            wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
            sheet = wb.active

            # Write to a temp file first then rename, so a partial write
            # can never leave a half-built CSV in place.
            tmp_path = csv_path + ".tmp"
            with open(tmp_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                for row in sheet.iter_rows(values_only=True):
                    writer.writerow(
                        ["" if v is None else v for v in row]
                    )
            wb.close()

            os.replace(tmp_path, csv_path)
            return True
        except Exception as e:
            print(f"[DataDownloader] xlsx->csv conversion failed: {e}")
            # Best-effort cleanup of partial output.
            try:
                if os.path.exists(csv_path + ".tmp"):
                    os.remove(csv_path + ".tmp")
            except OSError:
                pass
            return False
