import os
from datetime import timedelta

class Config:
    """Base application configuration with shared defaults.

    Contains settings for database, session management, file uploads,
    external API endpoints, and DeepSeek/Ollama LLM integration.
    Subclass this to create environment-specific configurations.
    """

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///skillsfuture.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'pdf'}
    JOBS_API_URL = 'https://data.gov.sg/api/action/datastore_search?resource_id=d_f3bbdfbf92b811fff364aeed23b5e0bb'
    COURSES_API_URL = 'https://api-open.data.gov.sg/v1/public/api/datasets/d_b5802b76f409764c16dde4bf2feb19cd/poll-download'
    DEEPSEEK_API_URL = os.environ.get('DEEPSEEK_API_URL') or 'http://localhost:11434/api/generate'
    DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL') or 'deepseek-r1:latest'
    DEBUG = False

class DevelopmentConfig(Config):
    """Development environment configuration.

    Enables debug mode and disables secure cookies so the app can
    run over plain HTTP on localhost.
    """

    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production environment configuration.

    Disables debug mode and enforces secure (HTTPS-only) session cookies.
    """

    DEBUG = False
    SESSION_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}