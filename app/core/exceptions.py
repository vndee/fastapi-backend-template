"""
Custom exception classes for the application
"""

from enum import StrEnum

from fastapi import HTTPException

from app.schemas.base import ErrorResponseSchema


class APIException(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: StrEnum,
    ):
        super().__init__(
            status_code=status_code,
            detail=ErrorResponseSchema(
                code=error_code,
                message=message,
            ).model_dump(),
        )
