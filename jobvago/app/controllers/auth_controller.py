from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from app.services.auth_service import AuthenticationService

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login via GET (render form) and POST (authenticate).

    On successful authentication the user is redirected to the dashboard
    or the 'next' page stored in the query string.  On failure an error
    flash message is displayed and the login form is re-rendered.

    Returns:
        Response: Rendered login template or redirect to dashboard.
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        success, user, message = AuthenticationService.authenticate_user(email, password)
        if success:
            login_user(user, remember=remember)
            flash(message, 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        else:
            flash(message, 'error')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle new user registration via GET (render form) and POST (create account).

    Validates that passwords match, delegates account creation to
    AuthenticationService, and automatically logs the user in on success.

    Returns:
        Response: Rendered registration template or redirect to dashboard.
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        success, user, message = AuthenticationService.register_user(email, password, full_name)
        if success:
            login_user(user)
            flash(message, 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash(message, 'error')
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """Log the current user out and redirect to the career index page.

    Returns:
        Response: Redirect to the public career landing page.
    """
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('career.index'))