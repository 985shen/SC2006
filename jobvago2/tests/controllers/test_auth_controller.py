"""Unit tests for the authentication controller routes."""

import pytest

class TestAuthRoutes:
    """Tests for the authentication controller endpoints."""

    def test_login_page_renders(self, client):
        """GET /auth/login returns the login page."""
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert b"log" in response.data.lower() or b"Login" in response.data

    def test_register_page_renders(self, client):
        """GET /auth/register returns the registration page."""
        response = client.get("/auth/register")
        assert response.status_code == 200

    def test_register_and_login(self, client):
        """A new user can register and is automatically logged in."""
        response = client.post("/auth/register", data={
            "email": "new@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "full_name": "New User"
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_register_password_mismatch(self, client):
        """Mismatched passwords show an error."""
        response = client.post("/auth/register", data={
            "email": "new@example.com",
            "password": "password123",
            "confirm_password": "different456",
            "full_name": "New User"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"match" in response.data.lower() or b"do not match" in response.data.lower()

    def test_login_valid_credentials(self, client, sample_user):
        """Valid credentials redirect to the dashboard."""
        response = client.post("/auth/login", data={
            "email": "test@example.com",
            "password": "password123"
        }, follow_redirects=False)
        assert response.status_code == 302

    def test_login_invalid_password(self, client, sample_user):
        """Invalid password re-renders the login page."""
        response = client.post("/auth/login", data={
            "email": "test@example.com",
            "password": "wrongpassword"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"invalid" in response.data.lower() or b"error" in response.data.lower()

    def test_logout(self, auth_client):
        """Logging out redirects to the public page."""
        response = auth_client.get("/auth/logout", follow_redirects=False)
        assert response.status_code == 302

    def test_login_page_redirects_when_authenticated(self, auth_client):
        """An already-logged-in user visiting /auth/login is redirected."""
        response = auth_client.get("/auth/login", follow_redirects=False)
        assert response.status_code == 302

    def test_register_page_redirects_when_authenticated(self, auth_client):
        """An already-logged-in user visiting /auth/register is redirected."""
        response = auth_client.get("/auth/register", follow_redirects=False)
        assert response.status_code == 302
