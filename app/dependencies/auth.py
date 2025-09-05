import uuid
from typing import Optional

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.codes import ResponseCode
from app.core.database import get_db
from app.core.exceptions import APIException
from app.repositories.user import UserRepository
from app.schemas.auth import CurrentUserSchema
from app.services.auth import AuthService
from app.services.user import UserService

security = HTTPBearer(auto_error=False)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Get user repository dependency"""
    return UserRepository(db)


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    """Get user service dependency"""
    return UserService(user_repository)


def get_auth_service(
    user_service: UserService = Depends(get_user_service),
) -> AuthService:
    """Get auth service dependency"""
    return AuthService(user_service)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> CurrentUserSchema:
    """
    Get current authenticated user.
    Raises 401 if no valid token is provided.
    """
    if not credentials:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Access token required",
            error_code=ResponseCode.ACCESS_TOKEN_NOT_PROVIDED,
        )

    return await auth_service.get_current_user(credentials.credentials)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> Optional[CurrentUserSchema]:
    """
    Get current authenticated user if token is provided.
    Returns None if no token or invalid token.
    """
    if not credentials:
        return None

    try:
        return await auth_service.get_current_user(credentials.credentials)
    except APIException:
        return None


async def get_current_active_user(
    current_user: CurrentUserSchema = Depends(get_current_user),
) -> CurrentUserSchema:
    """
    Get current active user.
    Raises 401 if user is not active.
    """
    if not current_user.is_active:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="User account is inactive",
            error_code=ResponseCode.USER_NOT_ACTIVE,
        )
    return current_user


async def get_current_verified_user(
    current_user: CurrentUserSchema = Depends(get_current_active_user),
) -> CurrentUserSchema:
    """
    Get current verified user.
    Raises 403 if user is not verified.
    """
    if not current_user.is_verified:
        raise APIException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="User account is not verified",
            error_code=ResponseCode.USER_NOT_VERIFIED,
        )
    return current_user


async def get_current_superuser(
    current_user: CurrentUserSchema = Depends(get_current_active_user),
) -> CurrentUserSchema:
    """
    Get current superuser.
    Raises 403 if user is not a superuser.
    """
    if not current_user.is_superuser:
        raise APIException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Not enough permissions",
            error_code=ResponseCode.FORBIDDEN,
        )
    return current_user


def require_permissions(*required_permissions: str):
    """
    Decorator factory for requiring specific permissions.
    Usage: @require_permissions("users:read", "users:write")
    """

    def permission_checker(
        current_user: CurrentUserSchema = Depends(get_current_active_user),
    ) -> CurrentUserSchema:
        # In a real implementation, you would check user permissions here
        # For this demo, we'll just check if user is verified
        if not current_user.is_verified and required_permissions:
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="User must be verified for this action",
                error_code=ResponseCode.USER_NOT_VERIFIED,
            )
        return current_user

    return permission_checker


def require_self_or_superuser(user_id: uuid.UUID):
    """
    Require that the current user is either the target user or a superuser.
    """

    def checker(
        current_user: CurrentUserSchema = Depends(get_current_active_user),
    ) -> CurrentUserSchema:
        if current_user.id != user_id and not current_user.is_superuser:
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ResponseCode.FORBIDDEN,
            )
        return current_user

    return checker
