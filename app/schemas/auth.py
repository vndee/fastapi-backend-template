import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class TokenData(BaseModel):
    """Token data for JWT payload"""

    user_id: Optional[uuid.UUID] = None
    username: Optional[str] = None
    email: Optional[str] = None
    is_superuser: bool = False
    is_verified: bool = False


class CurrentUserSchema(BaseModel):
    """Current authenticated user schema"""

    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    is_verified: bool
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoginResponseSchema(BaseModel):
    """Login response with user info and tokens"""

    user: CurrentUserSchema
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthStatusSchema(BaseModel):
    """Authentication status response"""

    is_authenticated: bool
    user: Optional[CurrentUserSchema] = None


class LogoutResponseSchema(BaseModel):
    """Logout response"""

    message: str = "Successfully logged out"
