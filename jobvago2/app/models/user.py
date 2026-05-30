from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

class User(db.Model, UserMixin):
    """SQLAlchemy model for authenticated users.

    Stores credentials, profile information, resume metadata, and provides
    helper methods for password management, login tracking, favourite
    courses, resume analyses, and skill storage.

    Attributes:
        id: Auto-incrementing primary key.
        email: Unique, indexed email address (normalised to lowercase).
        password_hash: Werkzeug-generated password hash.
        full_name: User's display name.
        created_at: Account creation timestamp.
        last_login: Most recent successful login timestamp.
        current_resume_path: Filesystem path to the user's active resume PDF.
        resume_uploaded_at: Timestamp of the most recent resume upload.
        favorite_courses: One-to-many relationship with FavoriteCourse.
        resume_analyses: One-to-many relationship with ResumeAnalysis.
    """
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Resume tracking
    current_resume_path = db.Column(db.String(500), nullable=True)
    resume_uploaded_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    favorite_courses = db.relationship('FavoriteCourse', backref='user', lazy=True, cascade='all, delete-orphan')
    resume_analyses = db.relationship('ResumeAnalysis', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        """Return a human-readable string representation of the User."""
        return f'<User {self.email}>'
    
    # ========================================================================
    # PASSWORD METHODS
    # ========================================================================
    
    def set_password(self, password):
        """Hash and set user password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    # ========================================================================
    # LOGIN TRACKING
    # ========================================================================
    
    def update_last_login(self):
        """Update the last login timestamp"""
        self.last_login = datetime.now(timezone.utc)
        db.session.commit()
    
    # ========================================================================
    # RESUME ANALYSIS METHODS
    # ========================================================================
    
    def get_resume_analyses(self):
        """Get all resume analyses for this user"""
        return ResumeAnalysis.query.filter_by(user_id=self.id).order_by(ResumeAnalysis.analyzed_at.desc()).all()
    
    def get_latest_analysis(self):
        """Get the most recent resume analysis"""
        return ResumeAnalysis.query.filter_by(user_id=self.id).order_by(ResumeAnalysis.analyzed_at.desc()).first()
    
    # ========================================================================
    # SKILLS METHODS
    # ========================================================================

    def set_skills(self, skills: list, source: str = 'fallback'):
        """Replace all stored skills for this user with a new list.

        Args:
            skills: list of dicts with keys 'skill' and optionally 'category'
            source: 'deepseek' or 'fallback'
        """
        # Delete existing skills
        UserSkill.query.filter_by(user_id=self.id).delete()
        for item in skills:
            us = UserSkill(
                user_id=self.id,
                skill=item['skill'],
                category=item.get('category', ''),
                source=source
            )
            db.session.add(us)
        db.session.commit()

    def get_skills(self):
        """Return list of UserSkill objects for this user, newest first."""
        return UserSkill.query.filter_by(user_id=self.id).order_by(UserSkill.extracted_at.desc()).all()

    def get_skill_names(self):
        """Return plain list of skill name strings."""
        return [s.skill for s in self.get_skills()]

    # ========================================================================
    # RESUME MANAGEMENT METHODS
    # ========================================================================
    
    def update_resume_path(self, resume_path: str):
        """
        Update the user's current resume path
        
        Args:
            resume_path: Path to the resume file
        """
        self.current_resume_path = resume_path
        self.resume_uploaded_at = datetime.now(timezone.utc)
        db.session.commit()
    
    def has_resume(self) -> bool:
        """Check if user has uploaded a resume"""
        return self.current_resume_path is not None
    
    def delete_resume(self):
        """Clear the user's resume path"""
        self.current_resume_path = None
        self.resume_uploaded_at = None
        db.session.commit()


class FavoriteCourse(db.Model):
    """SQLAlchemy model for a user's bookmarked/favourite courses.

    Each record links a user to a specific course by its generated course_id,
    storing a snapshot of the course title, provider, and language at the time
    of bookmarking.

    Attributes:
        id: Auto-incrementing primary key.
        user_id: Foreign key to the owning User.
        course_id: Deterministic hash identifier of the course.
        course_title: Snapshot of the course title.
        course_provider: Snapshot of the training provider name.
        course_language: Language of instruction (default 'English').
        added_at: Timestamp when the course was favourited.
    """
    
    __tablename__ = 'favorite_courses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.String(200), nullable=False)
    course_title = db.Column(db.String(200), nullable=False)
    course_provider = db.Column(db.String(200), nullable=False)
    course_language = db.Column(db.String(200), nullable=True, default='English')
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        """Return a human-readable string representation of the FavoriteCourse."""
        return f'<FavoriteCourse {self.course_title}>'


class ResumeAnalysis(db.Model):
    """SQLAlchemy model storing the results of a single resume analysis.

    Contains both the basic AI-generated feedback (score, feedback text,
    action verbs) and the VMock-style grading breakdown (impact,
    presentation, competencies).

    Attributes:
        id: Auto-incrementing primary key.
        user_id: Foreign key to the owning User.
        filename: Original uploaded filename.
        score: Overall action-verb score (1–10).
        feedback: Detailed textual feedback from the AI or fallback analyser.
        action_verbs_found: JSON-encoded list of action verbs detected.
        analyzed_at: Timestamp of the analysis.
        grade_total: VMock-style total grade (0–100).
        grade_impact: Impact sub-score (0–40).
        grade_presentation: Presentation sub-score (0–30).
        grade_competencies: Competencies sub-score (0–30).
        grade_breakdown: Full grading breakdown stored as a JSON string.
        grade_ollama_used: Whether the Ollama AI backend was available for grading.
    """
    
    __tablename__ = 'resume_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    feedback = db.Column(db.Text, nullable=False)
    action_verbs_found = db.Column(db.Text, nullable=True)
    analyzed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # VMock-style grading fields
    grade_total = db.Column(db.Integer, nullable=True)          # 0-100
    grade_impact = db.Column(db.Integer, nullable=True)         # 0-40
    grade_presentation = db.Column(db.Integer, nullable=True)   # 0-30
    grade_competencies = db.Column(db.Integer, nullable=True)   # 0-30
    grade_breakdown = db.Column(db.Text, nullable=True)         # JSON blob
    grade_ollama_used = db.Column(db.Boolean, nullable=True, default=False)

    def get_grade_breakdown(self):
        """Parse the JSON grade_breakdown column into a Python dict.

        Returns:
            dict | None: Parsed breakdown dictionary, or None if unavailable.
        """
        if self.grade_breakdown:
            try:
                import json
                return json.loads(self.grade_breakdown)
            except Exception:
                pass
        return None

    def __repr__(self):
        """Return a human-readable string representation of the ResumeAnalysis."""
        return f'<ResumeAnalysis {self.filename} - Score: {self.score}>'

class UserSkill(db.Model):
    """SQLAlchemy model for individual skills extracted from a user's resume.

    Each record represents one skill identified either by the DeepSeek AI
    model or by the regex-based fallback extractor.

    Attributes:
        id: Auto-incrementing primary key.
        user_id: Foreign key to the owning User.
        skill: Canonical skill name (e.g. 'Python', 'Project Management').
        category: Skill category such as 'Programming', 'Data & AI', 'Soft Skills'.
        source: Extraction method used — 'deepseek' or 'fallback'.
        extracted_at: Timestamp of when the skill was stored.
    """

    __tablename__ = 'user_skills'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=True)   # e.g. "Programming", "Data"
    source = db.Column(db.String(20), nullable=False, default='fallback')  # 'deepseek' | 'fallback'
    extracted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        """Return a human-readable string representation of the UserSkill."""
        return f'<UserSkill {self.skill} ({self.source})>'