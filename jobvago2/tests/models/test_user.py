"""Unit tests for the User model and related models."""

import pytest
from app import db
from app.models.user import User, FavoriteCourse, ResumeAnalysis, UserSkill
from app.services.favorite_course_service import FavoriteCourseService


class TestUserModel:
    """Tests for the User model."""

    def test_create_user(self, app):
        """A new user can be created with email, name, and password."""
        user = User(email="new@example.com", full_name="New User")
        user.set_password("secret123")
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.email == "new@example.com"
        assert user.full_name == "New User"

    def test_password_hashing(self, app):
        """Password is stored as a hash, not plaintext."""
        user = User(email="hash@example.com", full_name="Hash Test")
        user.set_password("mypassword")

        assert user.password_hash != "mypassword"
        assert user.check_password("mypassword") is True
        assert user.check_password("wrongpassword") is False

    def test_email_uniqueness(self, app, sample_user):
        """Duplicate emails are rejected by the database."""
        duplicate = User(email="test@example.com", full_name="Duplicate")
        duplicate.set_password("pass123")
        db.session.add(duplicate)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()

    def test_update_last_login(self, app, sample_user):
        """update_last_login sets the last_login timestamp."""
        assert sample_user.last_login is None
        sample_user.update_last_login()
        assert sample_user.last_login is not None

    def test_repr(self, app, sample_user):
        """__repr__ returns a readable string."""
        assert "test@example.com" in repr(sample_user)

    def test_has_resume_false_by_default(self, app, sample_user):
        """A new user has no resume."""
        assert sample_user.has_resume() is False

    def test_update_resume_path(self, app, sample_user):
        """update_resume_path sets the path and timestamp."""
        sample_user.update_resume_path("/tmp/resume.pdf")
        assert sample_user.current_resume_path == "/tmp/resume.pdf"
        assert sample_user.resume_uploaded_at is not None
        assert sample_user.has_resume() is True

    def test_delete_resume(self, app, sample_user):
        """delete_resume clears the path and timestamp."""
        sample_user.update_resume_path("/tmp/resume.pdf")
        sample_user.delete_resume()
        assert sample_user.current_resume_path is None
        assert sample_user.resume_uploaded_at is None
        assert sample_user.has_resume() is False


class TestFavoriteCourses:
    """Tests for the favourite courses functionality via FavoriteCourseService."""

    def test_add_favourite(self, app, sample_user):
        """Adding a favourite creates a FavoriteCourse record."""
        result = FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "SkillsFuture"
        )
        assert result is True
        favs = FavoriteCourseService.get_favorites(sample_user.id)
        assert len(favs) == 1
        assert favs[0].course_title == "Python 101"

    def test_add_duplicate_favourite(self, app, sample_user):
        """Adding the same course twice returns False."""
        FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "SkillsFuture"
        )
        result = FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "SkillsFuture"
        )
        assert result is False
        favs = FavoriteCourseService.get_favorites(sample_user.id)
        assert len(favs) == 1

    def test_remove_favourite(self, app, sample_user):
        """Removing a favourite deletes the FavoriteCourse record."""
        FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "SkillsFuture"
        )
        result = FavoriteCourseService.remove_favorite(sample_user.id, "c001")
        assert result is True
        favs = FavoriteCourseService.get_favorites(sample_user.id)
        assert len(favs) == 0

    def test_remove_nonexistent_favourite(self, app, sample_user):
        """Removing a course that isn't favourited returns False."""
        result = FavoriteCourseService.remove_favorite(
            sample_user.id, "nonexistent"
        )
        assert result is False

    def test_get_favorites(self, app, sample_user):
        """get_favorites returns all favourites ordered by added_at descending."""
        FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "Provider A"
        )
        FavoriteCourseService.add_favorite(
            sample_user.id, "c002", "Java 201", "Provider B"
        )
        favs = FavoriteCourseService.get_favorites(sample_user.id)
        assert len(favs) == 2

    def test_get_favorite_course_ids(self, app, sample_user):
        """get_favorite_course_ids returns a set of course IDs."""
        FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "Provider A"
        )
        FavoriteCourseService.add_favorite(
            sample_user.id, "c002", "Java 201", "Provider B"
        )
        ids = FavoriteCourseService.get_favorite_course_ids(sample_user.id)
        assert ids == {"c001", "c002"}


class TestUserSkills:
    """Tests for the skills functionality on User."""

    def test_set_skills(self, app, sample_user):
        """set_skills stores a list of skills."""
        skills = [
            {"skill": "Python", "category": "Programming"},
            {"skill": "SQL", "category": "Data & AI"},
        ]
        sample_user.set_skills(skills, source="fallback")
        stored = sample_user.get_skills()
        assert len(stored) == 2

    def test_set_skills_replaces_existing(self, app, sample_user):
        """set_skills replaces all previous skills."""
        sample_user.set_skills([{"skill": "Python"}], source="fallback")
        sample_user.set_skills([{"skill": "Java"}, {"skill": "Go"}], source="deepseek")
        names = sample_user.get_skill_names()
        assert "Python" not in names
        assert "Java" in names
        assert "Go" in names
        assert len(names) == 2

    def test_get_skill_names(self, app, sample_user):
        """get_skill_names returns plain string list."""
        sample_user.set_skills([
            {"skill": "React", "category": "Web Development"},
        ], source="fallback")
        assert sample_user.get_skill_names() == ["React"]


class TestResumeAnalysis:
    """Tests for the ResumeAnalysis model."""

    def test_create_analysis(self, app, sample_user):
        """A resume analysis record can be created."""
        analysis = ResumeAnalysis(
            user_id=sample_user.id,
            filename="resume.pdf",
            score=7,
            feedback="Good use of action verbs.",
            action_verbs_found='["developed", "led"]'
        )
        db.session.add(analysis)
        db.session.commit()

        assert analysis.id is not None
        assert analysis.score == 7

    def test_get_grade_breakdown_valid_json(self, app, sample_user):
        """get_grade_breakdown parses valid JSON."""
        analysis = ResumeAnalysis(
            user_id=sample_user.id,
            filename="test.pdf",
            score=8,
            feedback="Great",
            grade_breakdown='{"total": 85}'
        )
        db.session.add(analysis)
        db.session.commit()

        result = analysis.get_grade_breakdown()
        assert result == {"total": 85}

    def test_get_grade_breakdown_invalid_json(self, app, sample_user):
        """get_grade_breakdown returns None for invalid JSON."""
        analysis = ResumeAnalysis(
            user_id=sample_user.id,
            filename="test.pdf",
            score=5,
            feedback="OK",
            grade_breakdown="not json"
        )
        db.session.add(analysis)
        db.session.commit()

        assert analysis.get_grade_breakdown() is None

    def test_get_grade_breakdown_none(self, app, sample_user):
        """get_grade_breakdown returns None when field is empty."""
        analysis = ResumeAnalysis(
            user_id=sample_user.id,
            filename="test.pdf",
            score=5,
            feedback="OK"
        )
        db.session.add(analysis)
        db.session.commit()

        assert analysis.get_grade_breakdown() is None

    def test_user_get_resume_analyses(self, app, sample_user):
        """User.get_resume_analyses returns analyses in descending order."""
        for i in range(3):
            a = ResumeAnalysis(
                user_id=sample_user.id,
                filename=f"resume_{i}.pdf",
                score=i + 5,
                feedback=f"Feedback {i}"
            )
            db.session.add(a)
        db.session.commit()

        analyses = sample_user.get_resume_analyses()
        assert len(analyses) == 3

    def test_user_get_latest_analysis(self, app, sample_user):
        """User.get_latest_analysis returns the most recent analysis."""
        ids = []
        for i in range(3):
            a = ResumeAnalysis(
                user_id=sample_user.id,
                filename=f"resume_{i}.pdf",
                score=i + 5,
                feedback=f"Feedback {i}"
            )
            db.session.add(a)
            db.session.flush()
            ids.append(a.id)
        db.session.commit()

        latest = sample_user.get_latest_analysis()
        assert latest is not None
        assert latest.id == ids[-1]
