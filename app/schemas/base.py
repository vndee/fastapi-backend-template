from datetime import datetime
from typing import Generic, Optional, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field

T = TypeVar("T")


class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: Optional[datetime] = None


class PaginationRequestSchema(BaseModel):
    offset: int = Query(0, ge=0)
    limit: int = Query(20, ge=1, le=100)
    search: Optional[str] = None


class PaginationSchema(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)
    total: int = 0


class PaginatedResponseSchema(BaseModel, Generic[T]):
    items: list[T]
    pagination: PaginationSchema


class ErrorResponseSchema(BaseModel):
    code: str | None = None
    message: str | None = None


class SuccessResponseSchema(BaseModel):
    message: str
