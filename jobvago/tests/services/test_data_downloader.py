"""Unit tests for the DataDownloader service."""

import os
import time
import pytest
import tempfile
from app.services.data_downloader import DataDownloader


class TestDataDownloaderInit:
    """Tests for DataDownloader initialisation."""

    def test_creates_csv_directory(self):
        """The CSV directory is created on init if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_dir = os.path.join(tmpdir, "test_csv")
            assert not os.path.exists(csv_dir)
            DataDownloader("http://a", "http://b", csv_dir=csv_dir)
            assert os.path.isdir(csv_dir)

    def test_existing_csv_directory_not_error(self):
        """Initialising with an existing directory does not raise."""
        with tempfile.TemporaryDirectory() as tmpdir:
            DataDownloader("http://a", "http://b", csv_dir=tmpdir)

    def test_stores_urls(self):
        """API URLs are stored as instance attributes."""
        dl = DataDownloader("http://jobs", "http://courses", csv_dir="/tmp")
        assert dl.jobs_api_url == "http://jobs"
        assert dl.courses_api_url == "http://courses"


class TestShouldRefresh:
    """Tests for the cache staleness check."""

    def test_missing_file_should_refresh(self):
        """A non-existent file should always be refreshed."""
        dl = DataDownloader("a", "b", csv_dir="/tmp")
        assert dl._should_refresh("/tmp/nonexistent_test_file.xyz") is True

    def test_fresh_file_should_not_refresh(self):
        """A file created just now should not be refreshed."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            path = f.name
        try:
            dl = DataDownloader("a", "b", csv_dir="/tmp")
            assert dl._should_refresh(path) is False
        finally:
            os.unlink(path)

    def test_stale_file_should_refresh(self):
        """A file older than max_age_hours should be refreshed."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            path = f.name
        try:
            # Set modification time to 2 days ago
            two_days_ago = time.time() - 2 * 24 * 3600
            os.utime(path, (two_days_ago, two_days_ago))
            dl = DataDownloader("a", "b", csv_dir="/tmp")
            assert dl._should_refresh(path, max_age_hours=24) is True
        finally:
            os.unlink(path)

    def test_custom_max_age(self):
        """The max_age_hours parameter is respected."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            path = f.name
        try:
            # Set modification time to 2 hours ago
            two_hours_ago = time.time() - 2 * 3600
            os.utime(path, (two_hours_ago, two_hours_ago))
            dl = DataDownloader("a", "b", csv_dir="/tmp")
            # Should NOT refresh with 24h window
            assert dl._should_refresh(path, max_age_hours=24) is False
            # Should refresh with 1h window
            assert dl._should_refresh(path, max_age_hours=1) is True
        finally:
            os.unlink(path)


class TestDownloadMethods:
    """Tests for the download methods with cached files."""

    def test_job_vacancies_returns_cached(self):
        """download_job_vacancies_csv returns cached file without network call."""
        csv_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'CSV')
        csv_path = os.path.join(csv_dir, 'JobVacancies.csv')
        if not os.path.exists(csv_path):
            pytest.skip("JobVacancies.csv not available for cache test")
        dl = DataDownloader("http://a", "http://b", csv_dir=csv_dir)
        success, path = dl.download_job_vacancies_csv()
        assert success is True
        assert path.endswith('JobVacancies.csv')

    def test_courses_returns_cached(self):
        """download_skillsfuture_courses_csv returns cached file without network call."""
        csv_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'CSV')
        excel_path = os.path.join(csv_dir, 'SkillsFutureCourses.xlsx')
        if not os.path.exists(excel_path):
            pytest.skip("SkillsFutureCourses.xlsx not available for cache test")
        dl = DataDownloader("http://a", "http://b", csv_dir=csv_dir)
        success, path = dl.download_skillsfuture_courses_csv()
        assert success is True
        assert path.endswith('SkillsFutureCourses.xlsx')
