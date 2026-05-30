from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_class=Config):
    """Create and configure the Flask application using the factory pattern.

    Initializes extensions (SQLAlchemy, Flask-Login), registers all controller
    blueprints, sets up the user-loader callback, and creates database tables.

    Args:
        config_class: Configuration class to load (default: base Config).

    Returns:
        flask.Flask: The fully configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # One-line note about whether the optional C++ keyword matcher is active.
    # Purely informational — the app behaves identically either way.
    from app.services._fast import NATIVE_AVAILABLE
    print(
        "[jobvago] native keyword acceleration: "
        + ("ENABLED (jvfast)" if NATIVE_AVAILABLE
           else "disabled (pure-Python fallback; build with "
                "`python -m app.native.build` for the fast path)")
    )
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # User loader callback - CRITICAL for Flask-Login
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load a user from the database by their primary key.

        This callback is required by Flask-Login and is called on every
        request to restore the current user from the session.

        Args:
            user_id: The string representation of the user's primary key.

        Returns:
            User | None: The User instance if found, otherwise None.
        """
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.controllers.auth_controller import auth_bp
    from app.controllers.career_controller import career_bp
    from app.controllers.dashboard_controller import dashboard_bp
    from app.controllers.resume_controller import resume_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(career_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(resume_bp)

    # Build a single DataService and attach it to the app. Controllers
    # access it via `current_app.extensions['data_service']` instead of
    # constructing a fresh one per request — the parsed-file cache inside
    # it survives across requests, which is where most of the speedup
    # comes from on slower (Windows) machines.
    from app.services.data_service import DataService
    app.extensions['data_service'] = DataService(
        jobs_api_url=app.config['JOBS_API_URL'],
        courses_api_url=app.config['COURSES_API_URL'],
    )
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app