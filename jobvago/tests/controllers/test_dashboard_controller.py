"""Unit tests for the dashboard and public controller routes."""

import pytest

class TestDashboardRoutes:
    """Tests for the dashboard controller endpoints."""

    def test_dashboard_requires_login(self, client):
        """Unauthenticated access to /dashboard/ redirects to login."""
        response = client.get("/dashboard/", follow_redirects=False)
        assert response.status_code == 302
        assert "login" in response.headers.get("Location", "").lower()

    def test_dashboard_accessible_when_logged_in(self, auth_client):
        """Authenticated access to /dashboard/ returns 200."""
        response = auth_client.get("/dashboard/")
        assert response.status_code == 200

    def test_add_favourite_requires_login(self, client):
        """Unauthenticated POST to add favourite redirects to login."""
        response = client.post("/dashboard/favorites/add",
                               json={"course_id": "c1", "course_title": "Test", "course_provider": "P"},
                               follow_redirects=False)
        assert response.status_code == 302 or response.status_code == 401

    def test_add_favourite_missing_fields(self, auth_client):
        """POST with missing required fields returns 400."""
        response = auth_client.post("/dashboard/favorites/add",
                                    json={"course_id": "c1"},
                                    content_type="application/json")
        assert response.status_code == 400

    def test_add_and_remove_favourite(self, auth_client):
        """A course can be added and then removed from favourites."""
        # Add
        resp_add = auth_client.post("/dashboard/favorites/add",
                                    json={"course_id": "c1", "course_title": "Test", "course_provider": "P"},
                                    content_type="application/json")
        assert resp_add.status_code == 200
        data = resp_add.get_json()
        assert data["success"] is True

        # Remove
        resp_remove = auth_client.post("/dashboard/favorites/remove",
                                       json={"course_id": "c1"},
                                       content_type="application/json")
        assert resp_remove.status_code == 200
        assert resp_remove.get_json()["success"] is True

    def test_remove_nonexistent_favourite(self, auth_client):
        """Removing a course that isn't favourited returns 404."""
        response = auth_client.post("/dashboard/favorites/remove",
                                    json={"course_id": "nonexistent"},
                                    content_type="application/json")
        assert response.status_code == 404

    def test_analyses_page_requires_login(self, client):
        """Unauthenticated access to /dashboard/analyses redirects."""
        response = client.get("/dashboard/analyses", follow_redirects=False)
        assert response.status_code == 302


class TestPublicRoutes:
    """Tests for public-facing routes."""

    def test_career_index_accessible(self, client):
        """GET / returns the public career page (may fail if CSV data is missing, but should not crash)."""
        response = client.get("/")
        assert response.status_code == 200

    def test_resume_upload_requires_login(self, client):
        """GET /resume/upload redirects unauthenticated users."""
        response = client.get("/resume/upload", follow_redirects=False)
        assert response.status_code == 302
