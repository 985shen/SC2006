"""Unit tests for the IndustryService."""

import os
import pytest
from app.services.data_downloader import DataDownloader
from app.services.industry_service import IndustryService, ICON_MAP


class TestIconMap:
    """Tests for the ICON_MAP constant."""

    def test_icon_map_is_non_empty(self):
        """The icon map contains entries."""
        assert len(ICON_MAP) > 0

    def test_known_icons_present(self):
        """Key industry substrings have emoji icons."""
        assert 'information technology' in ICON_MAP
        assert 'healthcare' in ICON_MAP
        assert 'financial' in ICON_MAP


class TestIndustryService:
    """Tests for IndustryService.get_industries_data using cached CSV."""

    @pytest.fixture
    def service(self):
        csv_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'CSV')
        csv_path = os.path.join(csv_dir, 'JobVacancies.csv')
        if not os.path.exists(csv_path):
            pytest.skip("JobVacancies.csv not available")
        dl = DataDownloader("http://a", "http://b", csv_dir=csv_dir)
        return IndustryService(dl)

    def test_returns_success(self, service):
        """get_industries_data returns success=True with data."""
        success, industries, err = service.get_industries_data()
        assert success is True
        assert err == ""

    def test_returns_list_of_industries(self, service):
        """Result is a non-empty list of Industry objects."""
        _, industries, _ = service.get_industries_data()
        assert len(industries) > 0

    def test_max_ten_industries(self, service):
        """At most 10 industries are returned."""
        _, industries, _ = service.get_industries_data()
        assert len(industries) <= 10

    def test_sorted_by_vacancies_descending(self, service):
        """Industries are sorted by vacancies from highest to lowest."""
        _, industries, _ = service.get_industries_data()
        for i in range(len(industries) - 1):
            assert industries[i].vacancies >= industries[i + 1].vacancies

    def test_all_have_positive_vacancies(self, service):
        """Every returned industry has at least 1000 vacancies."""
        _, industries, _ = service.get_industries_data()
        for ind in industries:
            assert ind.vacancies >= 1000

    def test_all_have_icons(self, service):
        """Every industry has a non-empty icon string."""
        _, industries, _ = service.get_industries_data()
        for ind in industries:
            assert len(ind.icon) > 0

    def test_growth_rate_is_numeric(self, service):
        """Every industry has a numeric growth rate."""
        _, industries, _ = service.get_industries_data()
        for ind in industries:
            assert isinstance(ind.growth_rate, float)
