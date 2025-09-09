import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.core.codes import ResponseCode
from app.core.exceptions import APIException
from app.dependencies.auth import (
    get_current_superuser,
    get_user_service,
)
from app.schemas.auth import CurrentUserSchema
from app.schemas.base import (
    PaginatedResponseSchema,
    PaginationRequestSchema,
)
from app.schemas.user import (
    UserCreateSchema,
    UserResponseSchema,
    UserUpdateSchema,
)
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_service: Annotated[UserService, Depends(get_user_service)],
    user_data: Annotated[UserCreateSchema, Body(embed=True)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_superuser)],
):
    """
    Create a new user.
    Only superusers can create users.
    """
    return await user_service.create(user_data, current_user_id=current_user.id)


@router.get("", status_code=status.HTTP_200_OK)
async def get_users(
    pagination: Annotated[PaginationRequestSchema, Query(embed=True)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    _: Annotated[CurrentUserSchema, Depends(get_current_superuser)],
) -> PaginatedResponseSchema[UserResponseSchema]:
    """
    Get list of users with pagination and filtering.
    Only superusers can access this endpoint.
    """
    search_params = {}
    if pagination.search:
        search_params = {"email": pagination.search, "username": pagination.search}

    return await user_service.get_multi(
        skip=pagination.offset,
        limit=pagination.limit,
        filters={},
        search=search_params,
        include_count=True,
    )


@router.get("/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_by_id(
    user_id: Annotated[uuid.UUID, Path],
    user_service: Annotated[UserService, Depends(get_user_service)],
    _: Annotated[CurrentUserSchema, Depends(get_current_superuser)],
) -> UserResponseSchema:
    """
    Get a user by ID.
    Only superusers can access this endpoint.
    """
    user = await user_service.get_by_id(user_id)
    if not user:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="User not found",
            error_code=ResponseCode.USER_NOT_FOUND,
        )
    return user


@router.put("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_user(
    user_id: Annotated[uuid.UUID, Path],
    user_data: Annotated[UserUpdateSchema, Body(embed=True)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_superuser)],
) -> None:
    """
    Update a user by ID.
    Only superusers can update users.
    """
    updated_user = await user_service.update(
        user_id, user_data, current_user_id=current_user.id
    )
    if not updated_user:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="User not found",
            error_code=ResponseCode.USER_NOT_FOUND,
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: Annotated[uuid.UUID, Path],
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[CurrentUserSchema, Depends(get_current_superuser)],
) -> None:
    """
    Delete a user by ID (soft delete).
    Only superusers can delete users.
    """
    success = await user_service.soft_delete(user_id, current_user_id=current_user.id)
    if not success:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="User not found",
            error_code=ResponseCode.USER_NOT_FOUND,
        )
