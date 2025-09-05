import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import status
from passlib.context import CryptContext  # type: ignore[import-untyped]

from app.core.codes import ResponseCode
from app.core.exceptions import APIException
from app.core.logger import get_logger
from app.core.telemetry import get_tracer
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import (
    PasswordChangeSchema,
    UserCreateSchema,
    UserResponseSchema,
    UserUpdateSchema,
)
from app.services.base import BaseService

logger = get_logger(__name__)
tracer = get_tracer(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService(
    BaseService[User, UserCreateSchema, UserUpdateSchema, UserResponseSchema]
):
    def __init__(self, user_repository: UserRepository):
        super().__init__(user_repository, UserResponseSchema)
        self.user_repository = user_repository

    @staticmethod
    @tracer.start_as_current_span("hash_password")
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    @staticmethod
    @tracer.start_as_current_span("verify_password")
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @tracer.start_as_current_span("validate_create")
    async def _validate_create(self, obj_data: Dict[str, Any]) -> None:
        """Validate user creation data"""
        email = obj_data.get("email")
        username = obj_data.get("username")

        if email and self.user_repository.is_email_taken(email):
            logger.warning(
                f"Email {email} already exists", operation="create_user_validation"
            )
            raise APIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Email already registered",
                error_code=ResponseCode.DUPLICATE_EMAIL,
            )

        if username and self.user_repository.is_username_taken(username):
            logger.warning(
                f"Username {username} already exists",
                operation="create_user_validation",
            )
            raise APIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Username already taken",
                error_code=ResponseCode.DUPLICATE_USERNAME,
            )

    @tracer.start_as_current_span("validate_update")
    async def _validate_update(
        self, id: uuid.UUID, obj_data: Dict[str, Any], existing_entity: User
    ) -> None:
        """Validate user update data"""
        email = obj_data.get("email")
        username = obj_data.get("username")

        if email and self.user_repository.is_email_taken(email, exclude_user_id=id):
            logger.warning(
                f"Email {email} already exists for another user",
                operation="update_user_validation",
            )
            raise APIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Email already registered by another user",
                error_code=ResponseCode.DUPLICATE_EMAIL,
            )

        if username and self.user_repository.is_username_taken(
            username, exclude_user_id=id
        ):
            logger.warning(
                f"Username {username} already exists for another user",
                operation="update_user_validation",
            )
            raise APIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Username already taken by another user",
                error_code=ResponseCode.DUPLICATE_USERNAME,
            )

    @tracer.start_as_current_span("create")
    async def create(
        self, obj_in: UserCreateSchema, current_user_id: Optional[uuid.UUID] = None
    ) -> UserResponseSchema:
        """Create a new user with hashed password"""
        logger.info("Creating new user", operation="create_user")

        obj_data = obj_in.model_dump(exclude_unset=True)

        password = obj_data.pop("password")
        obj_data["hashed_password"] = self.hash_password(password)

        if current_user_id:
            obj_data["created_by"] = current_user_id
            obj_data["updated_by"] = current_user_id

        await self._validate_create(obj_data)

        user = self.repository.create(obj_data)

        await self._post_create(user)

        logger.info(
            f"Successfully created user with ID: {user.id}", operation="create_user"
        )

        user_dict = user.to_dict()
        user_dict["display_name"] = user.display_name
        return self.response_schema.model_validate(user_dict)

    @tracer.start_as_current_span("get_by_email")
    async def get_by_email(self, email: str) -> Optional[UserResponseSchema]:
        """Get user by email"""
        logger.info(f"Getting user by email: {email}", operation="get_user_by_email")

        user = self.user_repository.get_by_email(email)
        if user:
            user_dict = user.to_dict()
            user_dict["display_name"] = user.display_name
            return self.response_schema.model_validate(user_dict)

        logger.warning(
            f"User with email {email} not found", operation="get_user_by_email"
        )
        return None

    @tracer.start_as_current_span("get_by_username")
    async def get_by_username(self, username: str) -> Optional[UserResponseSchema]:
        """Get user by username"""
        logger.info(
            f"Getting user by username: {username}", operation="get_user_by_username"
        )

        user = self.user_repository.get_by_username(username)
        if user:
            user_dict = user.to_dict()
            user_dict["display_name"] = user.display_name
            return self.response_schema.model_validate(user_dict)

        logger.warning(
            f"User with username {username} not found", operation="get_user_by_username"
        )
        return None

    @tracer.start_as_current_span("get_by_email_or_username")
    async def get_by_email_or_username(
        self, identifier: str
    ) -> Optional[UserResponseSchema]:
        """Get user by email or username"""
        logger.info(
            f"Getting user by identifier: {identifier}",
            operation="get_user_by_identifier",
        )

        user = self.user_repository.get_by_email_or_username(identifier)
        if user:
            user_dict = user.to_dict()
            user_dict["display_name"] = user.display_name
            return self.response_schema.model_validate(user_dict)

        logger.warning(
            f"User with identifier {identifier} not found",
            operation="get_user_by_identifier",
        )
        return None

    @tracer.start_as_current_span("authenticate")
    async def authenticate(
        self, username_or_email: str, password: str
    ) -> Optional[UserResponseSchema]:
        """Authenticate user with username/email and password"""
        logger.info(
            f"Authenticating user: {username_or_email}", operation="authenticate_user"
        )

        user = self.user_repository.get_by_email_or_username(username_or_email)
        if not user:
            logger.warning(
                f"User {username_or_email} not found during authentication",
                operation="authenticate_user",
            )
            return None

        if not self.verify_password(password, user.hashed_password):
            logger.warning(
                f"Invalid password for user {username_or_email}",
                operation="authenticate_user",
            )
            return None

        if not user.is_active:
            logger.warning(
                f"User {username_or_email} is not active", operation="authenticate_user"
            )
            return None

        await self.update_last_login(user.id)

        logger.info(
            f"Successfully authenticated user: {username_or_email}",
            operation="authenticate_user",
        )

        user_dict = user.to_dict()
        user_dict["display_name"] = user.display_name
        return self.response_schema.model_validate(user_dict)

    @tracer.start_as_current_span("change_password")
    async def change_password(
        self, user_id: uuid.UUID, password_data: PasswordChangeSchema
    ) -> bool:
        """Change user password"""
        logger.info(
            f"Changing password for user: {user_id}", operation="change_password"
        )

        user = self.repository.get(user_id)
        if not user:
            logger.warning(
                f"User {user_id} not found for password change",
                operation="change_password",
            )
            return False

        if not self.verify_password(
            password_data.current_password, user.hashed_password
        ):
            logger.warning(
                f"Invalid current password for user {user_id}",
                operation="change_password",
            )
            raise APIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Current password is incorrect",
                error_code=ResponseCode.INVALID_PASSWORD,
            )

        new_hashed_password = self.hash_password(password_data.new_password)
        updated_user = self.repository.update(
            user_id, {"hashed_password": new_hashed_password}
        )

        if updated_user:
            logger.info(
                f"Successfully changed password for user: {user_id}",
                operation="change_password",
            )
            return True

        return False

    @tracer.start_as_current_span("update_last_login")
    async def update_last_login(self, user_id: uuid.UUID) -> bool:
        """Update user's last login timestamp"""
        return bool(self.repository.update(user_id, {"last_login": datetime.utcnow()}))

    @tracer.start_as_current_span("verify_user")
    async def verify_user(self, user_id: uuid.UUID) -> Optional[UserResponseSchema]:
        """Mark user as verified"""
        logger.info(f"Verifying user: {user_id}", operation="verify_user")

        updated_user = self.repository.update(user_id, {"is_verified": True})
        if updated_user:
            user_dict = updated_user.to_dict()
            user_dict["display_name"] = updated_user.display_name
            return self.response_schema.model_validate(user_dict)

        return None

    @tracer.start_as_current_span("deactivate_user")
    async def deactivate_user(self, user_id: uuid.UUID) -> bool:
        """Deactivate user account"""
        logger.info(f"Deactivating user: {user_id}", operation="deactivate_user")
        return bool(self.repository.update(user_id, {"is_active": False}))

    @tracer.start_as_current_span("activate_user")
    async def activate_user(self, user_id: uuid.UUID) -> bool:
        """Activate user account"""
        logger.info(f"Activating user: {user_id}", operation="activate_user")
        return bool(self.repository.update(user_id, {"is_active": True}))

    @tracer.start_as_current_span("get_by_id")
    async def get_by_id(self, id: uuid.UUID) -> Optional[UserResponseSchema]:
        """Override to add display_name"""
        user = self.repository.get(id)
        if user:
            user_dict = user.to_dict()
            user_dict["display_name"] = user.display_name
            return self.response_schema.model_validate(user_dict)
        return None
