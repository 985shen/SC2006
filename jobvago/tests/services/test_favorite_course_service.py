"""Unit tests for the FavoriteCourseService."""

import pytest
from app import db
from app.models.user import FavoriteCourse
from app.services.favorite_course_service import FavoriteCourseService


class TestFavoriteCourseServiceAdd:
    """Tests for adding favourites."""

    def test_add_favorite_success(self, app, sample_user):
        """A course can be favourited successfully."""
        result = FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "SkillsFuture", "English"
        )
        assert result is True

    def test_add_favorite_creates_record(self, app, sample_user):
        """Adding a favourite persists a FavoriteCourse row in the database."""
        FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "SkillsFuture"
        )
        record = FavoriteCourse.query.filter_by(
            user_id=sample_user.id, course_id="c001"
        ).first()
        assert record is not None
        assert record.course_title == "Python 101"
        assert record.course_provider == "SkillsFuture"

    def test_add_favorite_default_language(self, app, sample_user):
        """Language defaults to English when not provided."""
        FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "SkillsFuture"
        )
        record = FavoriteCourse.query.filter_by(course_id="c001").first()
        assert record.course_language == "English"

    def test_add_favorite_custom_language(self, app, sample_user):
        """A custom language is stored correctly."""
        FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "SkillsFuture", "Mandarin"
        )
        record = FavoriteCourse.query.filter_by(course_id="c001").first()
        assert record.course_language == "Mandarin"

    def test_add_duplicate_returns_false(self, app, sample_user):
        """Adding the same course_id twice returns False."""
        FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "SkillsFuture"
        )
        result = FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "SkillsFuture"
        )
        assert result is False

    def test_add_duplicate_does_not_create_second_record(self, app, sample_user):
        """A duplicate add does not insert a second row."""
        FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "SkillsFuture"
        )
        FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "SkillsFuture"
        )
        count = FavoriteCourse.query.filter_by(
            user_id=sample_user.id, course_id="c001"
        ).count()
        assert count == 1

    def test_different_users_can_favourite_same_course(self, app, sample_user):
        """Two different users can favourite the same course."""
        from app.models.user import User
        user2 = User(email="other@example.com", full_name="Other User")
        user2.set_password("pass123")
        db.session.add(user2)
        db.session.commit()

        r1 = FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "SkillsFuture"
        )
        r2 = FavoriteCourseService.add_favorite(
            user2.id, "c001", "Python 101", "SkillsFuture"
        )
        assert r1 is True
        assert r2 is True


class TestFavoriteCourseServiceRemove:
    """Tests for removing favourites."""

    def test_remove_existing_favourite(self, app, sample_user):
        """Removing an existing favourite returns True."""
        FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "SkillsFuture"
        )
        result = FavoriteCourseService.remove_favorite(sample_user.id, "c001")
        assert result is True

    def test_remove_deletes_record(self, app, sample_user):
        """Removing a favourite deletes the database row."""
        FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "SkillsFuture"
        )
        FavoriteCourseService.remove_favorite(sample_user.id, "c001")
        record = FavoriteCourse.query.filter_by(
            user_id=sample_user.id, course_id="c001"
        ).first()
        assert record is None

    def test_remove_nonexistent_returns_false(self, app, sample_user):
        """Removing a course that was never favourited returns False."""
        result = FavoriteCourseService.remove_favorite(
            sample_user.id, "nonexistent"
        )
        assert result is False

    def test_remove_only_affects_target_user(self, app, sample_user):
        """Removing a favourite for one user does not affect another user."""
        from app.models.user import User
        user2 = User(email="other@example.com", full_name="Other User")
        user2.set_password("pass123")
        db.session.add(user2)
        db.session.commit()

        FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "SkillsFuture"
        )
        FavoriteCourseService.add_favorite(
            user2.id, "c001", "Python 101", "SkillsFuture"
        )
        FavoriteCourseService.remove_favorite(sample_user.id, "c001")

        assert FavoriteCourseService.get_favorite_course_ids(sample_user.id) == set()
        assert FavoriteCourseService.get_favorite_course_ids(user2.id) == {"c001"}


class TestFavoriteCourseServiceQuery:
    """Tests for querying favourites."""

    def test_get_favorites_empty(self, app, sample_user):
        """A user with no favourites gets an empty list."""
        favs = FavoriteCourseService.get_favorites(sample_user.id)
        assert favs == []

    def test_get_favorites_returns_all(self, app, sample_user):
        """get_favorites returns all favourited courses."""
        FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "Provider A"
        )
        FavoriteCourseService.add_favorite(
            sample_user.id, "c002", "Java 201", "Provider B"
        )
        favs = FavoriteCourseService.get_favorites(sample_user.id)
        assert len(favs) == 2

    def test_get_favorite_course_ids_empty(self, app, sample_user):
        """A user with no favourites gets an empty set of IDs."""
        ids = FavoriteCourseService.get_favorite_course_ids(sample_user.id)
        assert ids == set()

    def test_get_favorite_course_ids(self, app, sample_user):
        """get_favorite_course_ids returns the correct set."""
        FavoriteCourseService.add_favorite(
            sample_user.id, "c001", "Python 101", "Provider A"
        )
        FavoriteCourseService.add_favorite(
            sample_user.id, "c002", "Java 201", "Provider B"
        )
        ids = FavoriteCourseService.get_favorite_course_ids(sample_user.id)
        assert ids == {"c001", "c002"}
