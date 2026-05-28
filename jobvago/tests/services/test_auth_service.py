"""Unit tests for the AuthenticationService."""

import pytest
from app.services.auth_service import AuthenticationService
from app.models.user import User
from app import db


class TestRegisterUser:
    """Tests for AuthenticationService.register_user."""

    def test_successful_registration(self, app):
        """Valid inputs create a user and return success."""
        success, user, msg = AuthenticationService.register_user(
            "new@example.com", "password123", "New User"
        )
        assert success is True
        assert user is not None
        assert user.email == "new@example.com"
        assert user.full_name == "New User"
        assert "successful" in msg.lower()

    def test_invalid_email_no_at(self, app):
        """An email without @ is rejected."""
        success, user, msg = AuthenticationService.register_user(
            "invalidemail", "password123", "User"
        )
        assert success is False
        assert user is None
        assert "email" in msg.lower()

    def test_empty_email(self, app):
        """An empty email is rejected."""
        success, user, msg = AuthenticationService.register_user(
            "", "password123", "User"
        )
        assert success is False

    def test_short_password(self, app):
        """A password shorter than 6 characters is rejected."""
        success, user, msg = AuthenticationService.register_user(
            "user@example.com", "12345", "User"
        )
        assert success is False
        assert "6 characters" in msg

    def test_empty_password(self, app):
        """An empty password is rejected."""
        success, user, msg = AuthenticationService.register_user(
            "user@example.com", "", "User"
        )
        assert success is False

    def test_short_name(self, app):
        """A name shorter than 2 characters is rejected."""
        success, user, msg = AuthenticationService.register_user(
            "user@example.com", "password123", "A"
        )
        assert success is False
        assert "name" in msg.lower()

    def test_empty_name(self, app):
        """An empty name is rejected."""
        success, user, msg = AuthenticationService.register_user(
            "user@example.com", "password123", ""
        )
        assert success is False

    def test_duplicate_email(self, app, sample_user):
        """Registering with an already-used email is rejected."""
        success, user, msg = AuthenticationService.register_user(
            "test@example.com", "password123", "Another User"
        )
        assert success is False
        assert "already registered" in msg.lower()

    def test_email_normalised_to_lowercase(self, app):
        """Emails are stored in lowercase."""
        success, user, _ = AuthenticationService.register_user(
            "USER@EXAMPLE.COM", "password123", "User"
        )
        assert success is True
        assert user.email == "user@example.com"

    def test_email_stripped(self, app):
        """Leading/trailing whitespace is stripped from emails."""
        success, user, _ = AuthenticationService.register_user(
            "  spaced@example.com  ", "password123", "User"
        )
        assert success is True
        assert user.email == "spaced@example.com"


class TestAuthenticateUser:
    """Tests for AuthenticationService.authenticate_user."""

    def test_successful_login(self, app, sample_user):
        """Valid credentials return success and the user object."""
        success, user, msg = AuthenticationService.authenticate_user(
            "test@example.com", "password123"
        )
        assert success is True
        assert user.id == sample_user.id
        assert user.last_login is not None

    def test_wrong_password(self, app, sample_user):
        """An incorrect password is rejected."""
        success, user, msg = AuthenticationService.authenticate_user(
            "test@example.com", "wrongpassword"
        )
        assert success is False
        assert user is None
        assert "invalid" in msg.lower()

    def test_nonexistent_email(self, app):
        """A non-registered email is rejected."""
        success, user, msg = AuthenticationService.authenticate_user(
            "nobody@example.com", "password123"
        )
        assert success is False
        assert user is None

    def test_empty_credentials(self, app):
        """Empty email and password are rejected."""
        success, user, msg = AuthenticationService.authenticate_user("", "")
        assert success is False

    def test_case_insensitive_email(self, app, sample_user):
        """Login works regardless of email casing."""
        success, user, _ = AuthenticationService.authenticate_user(
            "TEST@EXAMPLE.COM", "password123"
        )
        assert success is True
        assert user.id == sample_user.id
