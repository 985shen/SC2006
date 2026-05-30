"""Shared pytest fixtures for the JobVago2 test suite."""

import os
import sys
import pytest
import tempfile

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from config import Config


class TestConfig(Config):
    """Configuration for the test environment.

    Uses an in-memory SQLite database and disables CSRF protection
    so that form submissions work without tokens.
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"
    UPLOAD_FOLDER = tempfile.mkdtemp()
    DEEPSEEK_API_URL = "http://localhost:11434/api/generate"
    DEEPSEEK_MODEL = "deepseek-r1:latest"
    JOBS_API_URL = "https://example.com/jobs"
    COURSES_API_URL = "https://example.com/courses"


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_user(app):
    """Create and return a sample registered user."""
    from app.models.user import User
    user = User(email="test@example.com", full_name="Test User")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def auth_client(client, sample_user):
    """Return a test client that is already logged in as sample_user."""
    client.post("/auth/login", data={
        "email": "test@example.com",
        "password": "password123"
    }, follow_redirects=True)
    return client
