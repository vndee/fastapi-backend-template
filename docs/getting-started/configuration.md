# Configuration

The FastAPI Backend Template uses environment variables for configuration. This approach allows for easy deployment across different environments while keeping sensitive information secure.

## Environment File

The application reads configuration from a `.env` file in the project root. Start by copying the example:

```bash
cp .env.example .env
```

## Configuration Sections

### Application Settings

```bash
# Application Environment
ENVIRONMENT=development
APP_NAME=FastAPI Backend Template
SECRET_KEY=your-secret-key-here-change-in-production

# API Configuration
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

**Key Settings:**

- `ENVIRONMENT`: Set to `development`, `staging`, or `production`
- `SECRET_KEY`: Used for JWT token signing and other cryptographic operations
- `API_V1_PREFIX`: URL prefix for API endpoints
- `BACKEND_CORS_ORIGINS`: Allowed origins for CORS (JSON array format)

### Database Configuration

```bash
# PostgreSQL Database
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=0
```

**Database Settings:**

- `DATABASE_URL`: PostgreSQL connection string
- `DATABASE_POOL_SIZE`: Maximum number of persistent connections
- `DATABASE_MAX_OVERFLOW`: Additional connections beyond pool size

### Redis Configuration

```bash
# Redis Cache and Sessions
REDIS_URL=redis://localhost:6379
REDIS_CACHE_TTL=3600
```

**Redis Settings:**

- `REDIS_URL`: Redis connection string
- `REDIS_CACHE_TTL`: Default cache time-to-live in seconds

### Authentication

```bash
# JWT Authentication
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_MINUTES=10080
```

**Authentication Settings:**

- `JWT_SECRET_KEY`: Secret key for JWT token signing
- `JWT_ALGORITHM`: Algorithm for JWT signing (HS256 recommended)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Access token validity period
- `JWT_REFRESH_TOKEN_EXPIRE_MINUTES`: Refresh token validity period

### Celery Configuration

```bash
# Celery Task Queue
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379
CELERY_TASK_ALWAYS_EAGER=false
```

**Celery Settings:**

- `CELERY_BROKER_URL`: Message broker URL (typically Redis or RabbitMQ)
- `CELERY_RESULT_BACKEND`: Backend for storing task results
- `CELERY_TASK_ALWAYS_EAGER`: Execute tasks synchronously (for testing)

### OpenTelemetry Observability

```bash
# OpenTelemetry Configuration
OTEL_SERVICE_NAME=fastapi-backend-template
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_EXPORTER_OTLP_HEADERS=authorization=Bearer your-token
OTEL_RESOURCE_ATTRIBUTES=service.name=fastapi-backend-template,service.version=1.0.0
```

**Observability Settings:**

- `OTEL_SERVICE_NAME`: Service name for tracing
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OTLP collector endpoint
- `OTEL_EXPORTER_OTLP_HEADERS`: Authentication headers for collector
- `OTEL_RESOURCE_ATTRIBUTES`: Additional resource attributes

### Logging Configuration

```bash
# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_ENABLED=false
LOG_FILE_PATH=logs/app.log
```

**Logging Settings:**

- `LOG_LEVEL`: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FORMAT`: Log format (json or text)
- `LOG_FILE_ENABLED`: Enable file logging
- `LOG_FILE_PATH`: Path for log files

## Environment-Specific Configuration

### Development

```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://dev_user:dev_pass@localhost:5432/dev_db
CELERY_TASK_ALWAYS_EAGER=true
```

### Production

```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
SECRET_KEY=very-secure-production-secret-key
DATABASE_URL=postgresql://prod_user:secure_pass@prod-db:5432/prod_db
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]
```

## Security Considerations

!!! warning "Production Security"
    - Always use strong, unique secret keys in production
    - Never commit `.env` files to version control
    - Use environment variables or secure secret management in production
    - Regularly rotate secret keys and passwords

### Generating Secure Keys

Generate secure secret keys using:

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL
openssl rand -base64 32
```

## Configuration Loading

The application uses Pydantic Settings to load and validate configuration:

```python
# app/core/settings.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    environment: str = "development"
    app_name: str = "FastAPI Backend Template"
    secret_key: str
    
    class Config:
        env_file = ".env"
```

This provides:
- Automatic type conversion
- Validation of required fields
- Support for complex data types
- Environment variable precedence

## Next Steps

After configuring your environment:

1. [Quick Start](quick-start.md) - Run the application
2. [Architecture Overview](../architecture/overview.md) - Understand the application structure
3. [Development Guide](../development/environment.md) - Set up your development workflow