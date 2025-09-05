import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from fastapi import status

from app.core.codes import ResponseCode
from app.core.exceptions import APIException
from app.core.logger import get_logger
from app.core.settings import settings
from app.core.telemetry import get_tracer
from app.schemas.auth import CurrentUserSchema, LoginResponseSchema, TokenData
from app.schemas.user import LoginSchema, TokenRefreshSchema, TokenResponseSchema
from app.services.user import UserService

logger = get_logger(__name__)
tracer = get_tracer(__name__)


class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    @tracer.start_as_current_span("create_access_token")
    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )

        to_encode.update({"exp": expire, "type": "access"})

        try:
            encoded_jwt = jwt.encode(
                to_encode, settings.SECRET_KEY, algorithm=self.algorithm
            )
            logger.info(
                f"Created access token for user: {data.get('sub')}",
                operation="create_access_token",
            )
            return encoded_jwt
        except Exception as e:
            logger.error(
                f"Failed to create access token: {str(e)}",
                operation="create_access_token",
            )
            raise APIException(
                status_code=500,
                message="Failed to create access token",
                error_code=ResponseCode.INTERNAL_SERVER_ERROR,
            )

    @tracer.start_as_current_span("create_refresh_token")
    def create_refresh_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode.update({"exp": expire, "type": "refresh"})

        try:
            encoded_jwt = jwt.encode(
                to_encode, settings.SECRET_KEY, algorithm=self.algorithm
            )
            logger.info(
                f"Created refresh token for user: {data.get('sub')}",
                operation="create_refresh_token",
            )
            return encoded_jwt
        except Exception as e:
            logger.error(
                f"Failed to create refresh token: {str(e)}",
                operation="create_refresh_token",
            )
            raise APIException(
                status_code=500,
                message="Failed to create refresh token",
                error_code=ResponseCode.INTERNAL_SERVER_ERROR,
            )

    @tracer.start_as_current_span("verify_token")
    def verify_token(self, token: str, token_type: str = "access") -> TokenData:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[self.algorithm]
            )

            # Check token type
            if payload.get("type") != token_type:
                logger.warning(
                    f"Invalid token type. Expected: {token_type}, Got: {payload.get('type')}",
                    operation="verify_token",
                )
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    message="Invalid token type",
                    error_code=ResponseCode.INVALID_TOKEN,
                )

            user_id = payload.get("sub")
            if user_id is None:
                logger.warning("Token missing user ID", operation="verify_token")
                raise APIException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    message="Invalid token payload",
                    error_code=ResponseCode.INVALID_TOKEN_PAYLOAD,
                )

            token_data = TokenData(
                user_id=uuid.UUID(user_id),
                username=payload.get("username"),
                email=payload.get("email"),
                is_superuser=payload.get("is_superuser", False),
                is_verified=payload.get("is_verified", False),
            )

            logger.info(
                f"Successfully verified {token_type} token for user: {user_id}",
                operation="verify_token",
            )
            return token_data

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired", operation="verify_token")
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Token has expired",
                error_code=ResponseCode.TOKEN_EXPIRED,
            )
        except jwt.PyJWTError as e:
            logger.warning(f"Invalid token: {str(e)}", operation="verify_token")
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Could not validate credentials",
                error_code=ResponseCode.INVALID_TOKEN,
            )
        except ValueError as e:
            logger.warning(
                f"Invalid user ID in token: {str(e)}", operation="verify_token"
            )
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid token payload",
                error_code=ResponseCode.INVALID_TOKEN_PAYLOAD,
            )

    @tracer.start_as_current_span("login")
    async def login(self, login_data: LoginSchema) -> LoginResponseSchema:
        """Authenticate user and return tokens"""
        logger.info(
            f"Login attempt for: {login_data.username_or_email}", operation="login"
        )

        user = await self.user_service.authenticate(
            login_data.username_or_email, login_data.password
        )

        if not user:
            logger.warning(
                f"Authentication failed for: {login_data.username_or_email}",
                operation="login",
            )
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Incorrect username/email or password",
                error_code=ResponseCode.INVALID_CREDENTIALS,
            )

        if not user.is_active:
            logger.warning(
                f"Inactive user attempted login: {login_data.username_or_email}",
                operation="login",
            )
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="User account is inactive",
                error_code=ResponseCode.USER_NOT_ACTIVE,
            )

        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "is_superuser": user.is_superuser,
            "is_verified": user.is_verified,
        }

        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token({"sub": str(user.id)})

        logger.info(f"Successful login for user: {user.username}", operation="login")

        return LoginResponseSchema(
            user=CurrentUserSchema.model_validate(user.model_dump()),
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire_minutes * 60,
        )

    @tracer.start_as_current_span("refresh_token")
    async def refresh_token(
        self, refresh_data: TokenRefreshSchema
    ) -> TokenResponseSchema:
        """Refresh access token using refresh token"""
        logger.info("Token refresh attempt", operation="refresh_token")

        token_data = self.verify_token(refresh_data.refresh_token, token_type="refresh")
        if not token_data.user_id:
            logger.warning("Token missing user ID", operation="refresh_token")
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid token payload",
                error_code=ResponseCode.INVALID_TOKEN_PAYLOAD,
            )

        user = await self.user_service.get_by_id(token_data.user_id)
        if not user:
            logger.warning(
                f"User not found during token refresh: {token_data.user_id}",
                operation="refresh_token",
            )
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="User not found",
                error_code=ResponseCode.USER_NOT_FOUND,
            )

        if not user.is_active:
            logger.warning(
                f"Inactive user attempted token refresh: {token_data.user_id}",
                operation="refresh_token",
            )
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="User account is inactive",
                error_code=ResponseCode.USER_NOT_ACTIVE,
            )

        new_token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "is_superuser": user.is_superuser,
            "is_verified": user.is_verified,
        }

        access_token = self.create_access_token(new_token_data)
        new_refresh_token = self.create_refresh_token({"sub": str(user.id)})

        logger.info(
            f"Successfully refreshed token for user: {user.username}",
            operation="refresh_token",
        )

        return TokenResponseSchema(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=self.access_token_expire_minutes * 60,
        )

    @tracer.start_as_current_span("get_current_user")
    async def get_current_user(self, token: str) -> CurrentUserSchema:
        """Get current user from access token"""
        logger.info("Getting current user from token", operation="get_current_user")

        token_data = self.verify_token(token, token_type="access")
        if not token_data.user_id:
            logger.warning("Token missing user ID", operation="get_current_user")
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid token payload",
                error_code=ResponseCode.INVALID_TOKEN_PAYLOAD,
            )

        user = await self.user_service.get_by_id(token_data.user_id)
        if not user:
            logger.warning(
                f"User not found: {token_data.user_id}", operation="get_current_user"
            )
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="User not found",
                error_code=ResponseCode.USER_NOT_FOUND,
            )

        if not user.is_active:
            logger.warning(
                f"Inactive user: {token_data.user_id}", operation="get_current_user"
            )
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="User account is inactive",
                error_code=ResponseCode.USER_NOT_ACTIVE,
            )

        logger.info(
            f"Retrieved current user: {user.username}", operation="get_current_user"
        )
        return CurrentUserSchema.model_validate(user.model_dump())

    @tracer.start_as_current_span("logout")
    async def logout(self, user_id: uuid.UUID) -> bool:
        """Logout user (in a real implementation, you might invalidate tokens)"""
        logger.info(f"User logout: {user_id}", operation="logout")
        # In a complete implementation, you might:
        # 1. Add token to blacklist
        # 2. Clear refresh tokens from database
        # 3. Log the logout action
        return True
