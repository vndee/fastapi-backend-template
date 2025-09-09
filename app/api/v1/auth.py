from typing import Annotated

from fastapi import APIRouter, Body, Depends, status

from app.core.codes import ResponseCode
from app.core.exceptions import APIException
from app.dependencies.auth import (
    get_auth_service,
    get_current_active_user,
    get_user_service,
)
from app.schemas.auth import (
    AuthStatusSchema,
    CurrentUserSchema,
    LoginResponseSchema,
    LogoutResponseSchema,
)
from app.schemas.base import SuccessResponseSchema
from app.schemas.user import (
    LoginSchema,
    PasswordChangeSchema,
    TokenRefreshSchema,
    TokenResponseSchema,
    UserCreateSchema,
    UserResponseSchema,
)
from app.services.auth import AuthService
from app.services.user import UserService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: Annotated[UserCreateSchema, Body(embed=True)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponseSchema:
    """
    Register a new user account.
    Public endpoint - no authentication required.
    """
    return await user_service.create(user_data)


@router.post("/login")
async def login(
    login_data: Annotated[LoginSchema, Body(embed=True)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponseSchema:
    """
    Authenticate user and return access/refresh tokens.
    """
    return await auth_service.login(login_data)


@router.post("/refresh")
async def refresh_token(
    refresh_data: Annotated[TokenRefreshSchema, Body(embed=True)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponseSchema:
    """
    Refresh access token using refresh token.
    """
    return await auth_service.refresh_token(refresh_data)


@router.post("/logout")
async def logout(
    current_user: Annotated[CurrentUserSchema, Depends(get_current_active_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LogoutResponseSchema:
    """
    Logout current user.
    This endpoint invalidates the current session.
    """
    await auth_service.logout(current_user.id)
    return LogoutResponseSchema()


@router.get("/me")
async def get_current_user(
    current_user: Annotated[CurrentUserSchema, Depends(get_current_active_user)],
) -> CurrentUserSchema:
    """
    Get current authenticated user information.
    """
    return current_user


@router.get("/status")
async def auth_status(
    current_user: Annotated[CurrentUserSchema, Depends(get_current_active_user)],
) -> AuthStatusSchema:
    """
    Check authentication status.
    Returns user information if authenticated.
    """
    return AuthStatusSchema(
        is_authenticated=True,
        user=current_user,
    )


@router.post("/change-password")
async def change_current_user_password(
    password_data: Annotated[PasswordChangeSchema, Body(embed=True)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_active_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> SuccessResponseSchema:
    """
    Change current user's password.
    """
    success = await user_service.change_password(current_user.id, password_data)
    if not success:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Failed to change password",
            error_code=ResponseCode.BAD_REQUEST,
        )

    return SuccessResponseSchema(message="Password changed successfully")
