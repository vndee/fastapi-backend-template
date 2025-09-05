import uuid
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.telemetry import get_tracer
from app.models.user import User
from app.repositories.base import BaseRepository

tracer = get_tracer(__name__)


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(db, User)

    @tracer.start_as_current_span("get_by_email")
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        return self.db.query(self.model).filter(self.model.email == email).first()

    @tracer.start_as_current_span("get_by_username")
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(self.model).filter(self.model.username == username).first()

    @tracer.start_as_current_span("get_by_email_or_username")
    def get_by_email_or_username(self, identifier: str) -> Optional[User]:
        """Get user by email or username"""
        return (
            self.db.query(self.model)
            .filter(
                or_(self.model.email == identifier, self.model.username == identifier)
            )
            .first()
        )

    @tracer.start_as_current_span("is_email_taken")
    def is_email_taken(
        self, email: str, exclude_user_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Check if email is already taken by another user"""
        query = self.db.query(self.model).filter(self.model.email == email)
        if exclude_user_id:
            query = query.filter(self.model.id != exclude_user_id)

        return query.first() is not None

    @tracer.start_as_current_span("is_username_taken")
    def is_username_taken(
        self, username: str, exclude_user_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Check if username is already taken by another user"""
        query = self.db.query(self.model).filter(self.model.username == username)
        if exclude_user_id:
            query = query.filter(self.model.id != exclude_user_id)

        return query.first() is not None

    @tracer.start_as_current_span("get_active_users")
    def get_active_users(self, skip: int = 0, limit: int = 100):
        """Get only active users"""
        return (
            self.db.query(self.model)
            .filter(self.model.is_active.is_(True))
            .offset(skip)
            .limit(limit)
            .all()
        )

    @tracer.start_as_current_span("get_verified_users")
    def get_verified_users(self, skip: int = 0, limit: int = 100):
        """Get only verified users"""
        return (
            self.db.query(self.model)
            .filter(self.model.is_verified.is_(True))
            .offset(skip)
            .limit(limit)
            .all()
        )

    @tracer.start_as_current_span("get_superusers")
    def get_superusers(self, skip: int = 0, limit: int = 100):
        """Get only superusers"""
        return (
            self.db.query(self.model)
            .filter(self.model.is_superuser.is_(True))
            .offset(skip)
            .limit(limit)
            .all()
        )
