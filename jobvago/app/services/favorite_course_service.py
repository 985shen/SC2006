from typing import List, Set
from app.models.user import FavoriteCourse
from app import db


class FavoriteCourseService:
    """Service handling favourite course business logic.

    Provides static methods for adding, removing, and querying a user's
    bookmarked courses.  All database interactions for favourite courses
    are centralised here, keeping the User model focused on data
    representation only.
    """

    @staticmethod
    def add_favorite(user_id: int, course_id: str, course_title: str,
                     course_provider: str, course_language: str = 'English') -> bool:
        """Add a course to a user's favourites.

        Args:
            user_id: Primary key of the user.
            course_id: Deterministic hash identifier of the course.
            course_title: Snapshot of the course title.
            course_provider: Snapshot of the training provider name.
            course_language: Language of instruction (default 'English').

        Returns:
            bool: True if the course was added, False if already favourited.
        """
        existing = FavoriteCourse.query.filter_by(
            user_id=user_id,
            course_id=course_id
        ).first()

        if not existing:
            favorite = FavoriteCourse(
                user_id=user_id,
                course_id=course_id,
                course_title=course_title,
                course_provider=course_provider,
                course_language=course_language
            )
            db.session.add(favorite)
            db.session.commit()
            return True
        return False

    @staticmethod
    def remove_favorite(user_id: int, course_id: str) -> bool:
        """Remove a course from a user's favourites.

        Args:
            user_id: Primary key of the user.
            course_id: Deterministic hash identifier of the course.

        Returns:
            bool: True if the course was removed, False if not found.
        """
        favorite = FavoriteCourse.query.filter_by(
            user_id=user_id,
            course_id=course_id
        ).first()

        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_favorites(user_id: int) -> List[FavoriteCourse]:
        """Get all favourited courses for a user, newest first.

        Args:
            user_id: Primary key of the user.

        Returns:
            list[FavoriteCourse]: Ordered list of favourite course records.
        """
        return FavoriteCourse.query.filter_by(
            user_id=user_id
        ).order_by(FavoriteCourse.added_at.desc()).all()

    @staticmethod
    def get_favorite_course_ids(user_id: int) -> Set[str]:
        """Get the set of favourited course IDs for a user.

        Args:
            user_id: Primary key of the user.

        Returns:
            set[str]: Set of course_id strings.
        """
        favorites = FavoriteCourseService.get_favorites(user_id)
        return {fav.course_id for fav in favorites}