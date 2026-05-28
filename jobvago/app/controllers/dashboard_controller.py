from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.services.resume_analysis_service import ResumeAnalysisService
from app.services.data_service import DataService
from app.services.favorite_course_service import FavoriteCourseService
from flask import current_app, request

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    """Render the authenticated user's personal dashboard.

    Aggregates favourite courses, latest resume analysis, extracted skills,
    and skill-based course recommendations into a single overview page.

    Returns:
        Response: Rendered dashboard/index.html template.
    """
    favorites = FavoriteCourseService.get_favorites(current_user.id)
    resume_service = ResumeAnalysisService(api_url=current_app.config['DEEPSEEK_API_URL'], model=current_app.config['DEEPSEEK_MODEL'], upload_folder=current_app.config['UPLOAD_FOLDER'])
    analyses = resume_service.get_user_analyses(current_user.id)
    latest_analysis = analyses[0] if analyses else None
    # Get user skills and build course recommendations
    # Strategy: scan all courses and find those whose prerequisites
    # mention the user's own skills. Score by number of skill matches,
    # then rank by score descending, rating descending.
    user_skills = current_user.get_skills()
    recommended_courses = []
    if user_skills:
        data_service = DataService(
            jobs_api_url=current_app.config['JOBS_API_URL'],
            courses_api_url=current_app.config['COURSES_API_URL']
        )
        # Build a lowercase list of the user's skill names for matching
        skill_names_lower = [s.skill.lower() for s in user_skills]

        # Load all courses without any industry filter so we get full coverage
        _, all_courses, _ = data_service.get_courses_data(industry=None)

        # Build a lookup dict so favorites can access course details
        course_map = {c.course_id: c for c in all_courses}

        scored = []
        for course in all_courses:
            if not course.prerequisites:
                continue
            prereq_lower = course.prerequisites.lower()
            match_count = sum(1 for skill in skill_names_lower if skill in prereq_lower)
            if match_count > 0:
                scored.append((match_count, course.rating, course))

        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        recommended_courses = [c for _, _, c in scored[:6]]
    else:
        # Still build course_map for favorites even if user has no skills
        if favorites:
            data_service = DataService(
                jobs_api_url=current_app.config['JOBS_API_URL'],
                courses_api_url=current_app.config['COURSES_API_URL']
            )
            _, all_courses, _ = data_service.get_courses_data(industry=None)
            course_map = {c.course_id: c for c in all_courses}
        else:
            course_map = {}

    return render_template('dashboard/index.html',
        favorites=favorites,
        latest_analysis=latest_analysis,
        total_favorites=len(favorites),
        total_analyses=len(analyses),
        user_skills=user_skills,
        recommended_courses=recommended_courses,
        course_map=course_map
    )

@dashboard_bp.route('/favorites/add', methods=['POST'])
@login_required
def add_favorite():
    """Add a course to the current user's favourites via JSON POST.

    Expects JSON body with course_id, course_title, course_provider,
    and optionally course_language.

    Returns:
        Response: JSON indicating success or failure with an HTTP status code.
    """
    data = request.get_json()
    course_id = data.get('course_id')
    course_title = data.get('course_title')
    course_provider = data.get('course_provider')
    course_language = data.get('course_language', 'English')
    if not all([course_id, course_title, course_provider]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    success = FavoriteCourseService.add_favorite(current_user.id, course_id, course_title, course_provider, course_language)
    if success:
        return jsonify({'success': True, 'message': 'Course added to favorites'})
    else:
        return jsonify({'success': False, 'message': 'Course already in favorites'}), 400

@dashboard_bp.route('/favorites/remove', methods=['POST'])
@login_required
def remove_favorite():
    """Remove a course from the current user's favourites via JSON POST.

    Expects JSON body with course_id.

    Returns:
        Response: JSON indicating success or failure with an HTTP status code.
    """
    data = request.get_json()
    course_id = data.get('course_id')
    if not course_id:
        return jsonify({'success': False, 'message': 'Missing course ID'}), 400
    success = FavoriteCourseService.remove_favorite(current_user.id, course_id)
    if success:
        return jsonify({'success': True, 'message': 'Course removed from favorites'})
    else:
        return jsonify({'success': False, 'message': 'Course not found in favorites'}), 404

@dashboard_bp.route('/analyses')
@login_required
def analyses():
    """Display all past resume analyses for the authenticated user.

    Returns:
        Response: Rendered dashboard/analyses.html template.
    """
    resume_service = ResumeAnalysisService(api_url=current_app.config['DEEPSEEK_API_URL'], model=current_app.config['DEEPSEEK_MODEL'], upload_folder=current_app.config['UPLOAD_FOLDER'])
    all_analyses = resume_service.get_user_analyses(current_user.id)
    return render_template('dashboard/analyses.html', analyses=all_analyses)