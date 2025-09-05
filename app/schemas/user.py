import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.isalnum() and "_" not in v and "-" not in v:
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )
        return v.lower()


class UserCreateSchema(UserBase):
    password: str = Field(..., min_length=8, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdateSchema(BaseModel):
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None


class UserResponseSchema(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class PasswordChangeSchema(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=255)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# Password Reset Schema
class PasswordResetRequestSchema(BaseModel):
    email: EmailStr


class PasswordResetSchema(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=255)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginSchema(BaseModel):
    username_or_email: str
    password: str


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefreshSchema(BaseModel):
    refresh_token: str


class UserProfileUpdateSchema(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) == 0:
            return None
        return v
