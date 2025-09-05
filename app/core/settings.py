import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local", ".env.development"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Application
    ENVIRONMENT: str = "development"
    APP_NAME: str = "FastAPI Backend Template"
    APP_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = secrets.token_urlsafe(32)

    # Server
    BASE_URL: str = "http://localhost:8000"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    RELOAD: bool = False

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/backend"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_TIMEOUT: int = 30
    DB_CONNECT_TIMEOUT: int = 10
    DB_POOL_PRE_PING: bool = False

    # Redis
    REDIS_URL: str = "redis://redis:6379"
    REDIS_MAX_CONNECTIONS: int = 100

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Monitoring
    OTEL_ENABLED: bool = False
    OTEL_SERVICE_NAME: str = "fastapi-backend-template"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    OTEL_EXPORTER_OTLP_PROTOCOL: str = "grpc"
    OTEL_EXPORTER_OTLP_HEADERS: str = "authorization=Bearer <your-token>"

    @property
    def database_pool_config(self) -> dict:
        """Get environment-specific database connection pool configuration."""
        if self.ENVIRONMENT == "production":
            return {
                "pool_size": 20,
                "max_overflow": 30,
                "pool_recycle": 3600,
                "pool_timeout": 30,
                "pool_pre_ping": True,
            }
        elif self.ENVIRONMENT == "staging":
            return {
                "pool_size": 10,
                "max_overflow": 15,
                "pool_recycle": 1800,
                "pool_timeout": 20,
                "pool_pre_ping": True,
            }
        else:  # development
            return {
                "pool_size": self.DB_POOL_SIZE,
                "max_overflow": self.DB_MAX_OVERFLOW,
                "pool_recycle": self.DB_POOL_RECYCLE,
                "pool_timeout": self.DB_POOL_TIMEOUT,
                "pool_pre_ping": self.DB_POOL_PRE_PING,
            }


settings = Settings()
