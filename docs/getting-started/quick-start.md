# Quick Start

This guide will get you up and running with the FastAPI Backend Template in just a few minutes.

## Prerequisites

Ensure you have completed the [Installation](installation.md) and [Configuration](configuration.md) steps before proceeding.

## Starting the Application

### 1. Start Required Services

First, start PostgreSQL and Redis:

```bash
docker-compose up -d postgres redis
```

Verify services are running:

```bash
docker-compose ps
```

### 2. Run Database Migrations

Apply the initial database schema:

```bash
make db-upgrade
```

### 3. Start the Development Server

Launch the FastAPI application:

```bash
make dev
```

The application will start on http://localhost:8000 with hot-reload enabled for development.

## Exploring the API

### Interactive Documentation

Visit the automatically generated API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Health Check

Test that the application is running correctly:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "environment": "development",
  "version": "0.1.0"
}
```

## Basic API Usage

### 1. Create a User

Create a new user account:

```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "full_name": "John Doe"
  }'
```

### 2. Authenticate

Get an access token:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepassword123"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 3. Access Protected Endpoints

Use the access token to call protected endpoints:

```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Development Workflow

### Code Quality Checks

Run linting and formatting:

```bash
# Check code quality
make check

# Format code
make format

# Run type checking
make type-check
```

### Testing

Run the test suite:

```bash
# Run all tests
make test

# Run with coverage
make test-cov
```

### Background Tasks

Start Celery worker for background tasks:

```bash
# Start worker
make celery-worker-dummy

# Monitor tasks (in another terminal)
make celery-flower
```

Visit http://localhost:5555 to access Flower monitoring UI.

## Project Structure Overview

Here's a quick overview of the key directories:

```
fastapi-backend-template/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── core/            # Core configuration
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic models
│   ├── services/        # Business logic
│   └── repositories/    # Data access
├── alembic/             # Database migrations
├── tests/               # Test suite
└── docs/                # Documentation
```

### Key Files

- `app/cmd/main.py` - Application entry point
- `app/core/settings.py` - Configuration management
- `app/api/v1/` - API route definitions
- `alembic/versions/` - Database migration scripts

## Next Steps

Now that you have the application running, explore these areas:

### Learn the Architecture
- [Architecture Overview](../architecture/overview.md) - Understand the design patterns
- [Clean Architecture](../architecture/clean-architecture.md) - Learn about the layered approach
- [Database Design](../architecture/database.md) - Explore the data model

### Develop Features
- [Development Environment](../development/environment.md) - Set up your dev tools
- [Testing Guide](../development/testing.md) - Write and run tests
- [API Development](../api/endpoints.md) - Create new endpoints

### Deploy to Production
- [Docker Deployment](../deployment/docker.md) - Containerize the application
- [Production Setup](../deployment/production.md) - Deploy to production
- [Monitoring](../deployment/monitoring.md) - Set up observability

## Troubleshooting

### Common Issues

**Application won't start**
```bash
# Check if services are running
docker-compose ps

# Check logs
docker-compose logs postgres redis
```

**Database connection errors**
```bash
# Verify database URL in .env
cat .env | grep DATABASE_URL

# Test connection
make db-upgrade
```

**Import errors**
```bash
# Reinstall dependencies
make dev-install

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

**Port already in use**
```bash
# Check what's using port 8000
lsof -i :8000

# Kill the process or use a different port
uvicorn app.cmd.main:app --host 0.0.0.0 --port 8001 --reload
```

For more help, check the [Development Guide](../development/environment.md) or create an issue in the repository.