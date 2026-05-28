from typing import Tuple, Optional
from app.models.user import User
from app import db

class AuthenticationService:
    """Stateless service handling user registration and login authentication.

    All methods are static and interact directly with the User model and
    the application database session.  Returns standardised tuples of
    (success, user_or_none, message) for consistent controller handling.
    """

    @staticmethod
    def register_user(email: str, password: str, full_name: str) -> Tuple[bool, Optional[User], str]:
        """Register a new user account after validating inputs.

        Checks for valid email format, minimum password length, non-empty name,
        and email uniqueness before creating the account.

        Args:
            email: The user's email address.
            password: The plaintext password (min 6 characters).
            full_name: The user's display name (min 2 characters after trimming).

        Returns:
            Tuple of (success, User | None, status_message).
        """
        if not email or '@' not in email:
            return False, None, "Invalid email address"
        if not password or len(password) < 6:
            return False, None, "Password must be at least 6 characters"
        if not full_name or len(full_name.strip()) < 2:
            return False, None, "Full name is required"
        
        existing_user = User.query.filter_by(email=email.lower().strip()).first()
        if existing_user:
            return False, None, "Email already registered"
        
        try:
            user = User(email=email.lower().strip(), full_name=full_name.strip())
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return True, user, "Registration successful"
        except Exception as e:
            db.session.rollback()
            return False, None, f"Registration failed: {str(e)}"
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> Tuple[bool, Optional[User], str]:
        """Authenticate a user by email and password.

        Looks up the user by normalised email and verifies the password
        hash.  Updates the last_login timestamp on success.

        Args:
            email: The user's email address.
            password: The plaintext password to verify.

        Returns:
            Tuple of (success, User | None, status_message).
        """
        if not email or not password:
            return False, None, "Email and password are required"
        
        user = User.query.filter_by(email=email.lower().strip()).first()
        if not user:
            return False, None, "Invalid email or password"
        if not user.check_password(password):
            return False, None, "Invalid email or password"
        
        user.update_last_login()
        return True, user, "Login successful"