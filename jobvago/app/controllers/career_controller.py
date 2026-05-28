from flask import Blueprint, render_template, current_app, request
from flask_login import current_user
from app.services.data_service import DataService
from app.services.favorite_course_service import FavoriteCourseService

career_bp = Blueprint('career', __name__)

@career_bp.route('/')
def index():
    """Render the public career landing page with industry stats and courses.

    Loads dashboard statistics, industry rankings, and courses for the
    top-ranked industry.  Accepts optional query-string filter parameters
    (impact_level, mode, sort_by, language).

    Returns:
        Response: Rendered career/index.html template.
    """
    data_service = DataService(
        jobs_api_url=current_app.config['JOBS_API_URL'],
        courses_api_url=current_app.config['COURSES_API_URL']
    )

    # Get filter parameters from query string
    filters = {
        'impact_level': request.args.get('impact_level', 'All Impact Levels'),
        'mode': request.args.get('mode', 'All Modes'),
        'sort_by': request.args.get('sort_by', 'Highest Rating'),
        'language': request.args.get('language', 'All Languages')
    }

    stats = data_service.get_dashboard_stats()
    success, industries, error = data_service.get_industries_data()

    # Use the #1 ranked industry (sorted by vacancies) as the default
    default_industry = industries[0].name if industries else "Information Technology"

    success_courses, courses, error_courses = data_service.get_courses_data(
        industry=default_industry,
        filters=filters
    )

    # Check which courses are favorited (if user is logged in)
    favorited_course_ids = []
    if current_user.is_authenticated:
        favorited_course_ids = list(FavoriteCourseService.get_favorite_course_ids(current_user.id))

    return render_template(
        'career/index.html',
        stats=stats,
        industries=industries,
        courses=courses,
        selected_industry=default_industry,
        favorited_course_ids=favorited_course_ids,
        filters=filters,
        industries_error=error if not success else None,
        courses_error=error_courses if not success_courses else None
    )

@career_bp.route('/industry/<industry_name>')
def industry_detail(industry_name):
    """Display courses filtered by a specific industry.

    Accepts the same query-string filter parameters as the index route
    and renders the same template with industry-specific course data.

    Args:
        industry_name: URL-decoded industry name to filter courses by.

    Returns:
        Response: Rendered career/index.html template scoped to the industry.
    """
    data_service = DataService(
        jobs_api_url=current_app.config['JOBS_API_URL'],
        courses_api_url=current_app.config['COURSES_API_URL']
    )

    # Get filter parameters from query string
    filters = {
        'impact_level': request.args.get('impact_level', 'All Impact Levels'),
        'mode': request.args.get('mode', 'All Modes'),
        'sort_by': request.args.get('sort_by', 'Highest Rating'),
        'language': request.args.get('language', 'All Languages')
    }

    stats = data_service.get_dashboard_stats()
    success, industries, error = data_service.get_industries_data()
    success_courses, courses, error_courses = data_service.get_courses_data(
        industry=industry_name,
        filters=filters
    )

    # Check which courses are favorited (if user is logged in)
    favorited_course_ids = []
    if current_user.is_authenticated:
        favorited_course_ids = list(FavoriteCourseService.get_favorite_course_ids(current_user.id))

    return render_template(
        'career/index.html',
        stats=stats,
        industries=industries,
        industries_error=error if not success else None,
        courses_error=error_courses if not success_courses else None,
        courses=courses,
        selected_industry=industry_name,
        favorited_course_ids=favorited_course_ids,
        filters=filters
    )