# FastAPI Backend Template

A production-ready FastAPI backend template with modern Python stack, featuring clean architecture, comprehensive observability, and development best practices.

## 🚀 Features

### Core Stack
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy 2.0** - Powerful ORM with async support
- **Alembic** - Database migration management
- **PostgreSQL** - Robust relational database
- **Redis** - High-performance caching and session storage
- **Celery** - Distributed task processing
- **UV** - Ultra-fast Python package manager

### Architecture & Design
- **Clean Architecture** - Domain-driven design with clear separation of concerns
- **Repository Pattern** - Data access abstraction layer
- **Dependency Injection** - Testable and maintainable code structure
- **Pydantic V2** - Data validation and serialization with type safety

### Observability & Monitoring
- **OpenTelemetry** - Distributed tracing and observability
- **Structured Logging** - JSON-formatted logs with correlation IDs
- **Health Checks** - Application and dependency health monitoring
- **Metrics Collection** - Performance and business metrics

### Development Experience
- **Pre-commit Hooks** - Automated code quality checks
- **Ruff** - Lightning-fast linting and formatting
- **MyPy** - Static type checking
- **Comprehensive Makefile** - Development workflow automation
- **Docker Support** - Containerized development and deployment

### Security & Authentication
- **JWT Authentication** - Secure token-based authentication
- **Password Hashing** - Bcrypt for secure password storage
- **Input Validation** - Pydantic-based request validation
- **CORS Middleware** - Cross-origin resource sharing configuration

## 📁 Project Structure

```
fastapi-backend-template/
├── alembic/
│   ├── versions/         # Migration scripts
│   ├── env.py           # Alembic environment
│   └── script.py.mako   # Migration template
├── app/
│   ├── api/v1/          # API route definitions
│   │   ├── auth.py      # Authentication endpoints
│   │   ├── health.py    # Health check endpoints
│   │   ├── task.py      # Task management endpoints
│   │   └── users.py     # User management endpoints
│   ├── cmd/
│   │   └── main.py      # Application entrypoint
│   ├── core/            # Core application components
│   │   ├── celery_config.py  # Celery configuration
│   │   ├── database.py       # Database setup
│   │   ├── settings.py       # Application settings
│   │   └── telemetry.py      # OpenTelemetry setup
│   ├── dependencies/    # Dependency injection
│   ├── middlewares/     # Custom middlewares
│   ├── models/          # SQLAlchemy models
│   ├── repositories/    # Data access layer
│   ├── schemas/         # Pydantic models
│   ├── services/        # Business logic layer
│   └── tasks/           # Celery tasks
├── scripts/             # Utility scripts and automation
├── tests/               # Test suite
│   ├── conftest.py      # Test configuration and fixtures
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── api/             # API endpoint tests
├── alembic.ini          # Alembic configuration
├── Makefile             # Development commands
├── pyproject.toml       # Project dependencies
└── uv.lock              # Dependency lock file
```

## 🛠 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis
- UV package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fastapi-backend-template
   ```

2. **Install dependencies**
   ```bash
   make dev-install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start services with Docker**
   ```bash
   docker-compose up -d postgres redis
   ```

5. **Run database migrations**
   ```bash
   make db-upgrade
   ```

6. **Start the application**
   ```bash
   make dev
   ```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## 📋 Development Commands

### Application
```bash
make dev          # Start development server
make run          # Start production server
make shell        # Python REPL with app context
```

### Code Quality
```bash
make lint         # Run linting checks
make format       # Format code
make type-check   # Run type checking
make check        # Run all quality checks
```

### Database
```bash
make db-upgrade   # Apply migrations
make db-downgrade # Rollback migration
make db-revision MESSAGE="description"  # Create new migration
make db-reset     # Reset database
```

### Celery Tasks
```bash
make celery-worker-dummy  # Start Celery worker
make celery-beat          # Start Celery scheduler
make celery-flower        # Start Flower monitoring UI
make celery-monitor       # Show task/worker stats
```

### Testing
```bash
make test         # Run tests
make test-cov     # Run tests with coverage
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Application
ENVIRONMENT=development
APP_NAME=FastAPI Backend Template
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379

# OpenTelemetry
OTEL_SERVICE_NAME=fastapi-backend-template
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_EXPORTER_OTLP_HEADERS=authorization=Bearer your-token

# Logging
LOG_LEVEL=INFO
```

### OpenTelemetry Setup

The application includes comprehensive observability with OpenTelemetry:

- **Distributed Tracing** - Track requests across services
- **Metrics Collection** - Application and business metrics
- **Log Correlation** - Structured logging with trace context
- **Export to OTLP** - Compatible with Jaeger, Zipkin, and observability platforms

Configure your observability backend by setting `OTEL_EXPORTER_OTLP_ENDPOINT` and authentication headers.

## 🏗 Architecture Overview

### Clean Architecture Layers

1. **API Layer** (`app/api/`) - HTTP endpoints and request/response handling
2. **Service Layer** (`app/services/`) - Business logic and orchestration
3. **Repository Layer** (`app/repositories/`) - Data access abstraction
4. **Model Layer** (`app/models/`) - Domain entities and database models

### Key Components

- **Dependencies** - FastAPI dependency injection for auth, database, etc.
- **Middlewares** - Request/response processing and CORS handling
- **Schemas** - Pydantic models for request/response validation
- **Tasks** - Asynchronous background job processing with Celery

## 🧪 Testing

The project follows testing best practices:

- **Unit Tests** - Test individual components in isolation
- **Integration Tests** - Test component interactions
- **API Tests** - End-to-end API testing
- **Fixtures** - Reusable test data and setup

Run the test suite:

```bash
make test           # Basic test run
make test-cov       # With coverage report
```

## 🚀 Deployment

### Docker

Build and run with Docker:

```bash
make docker-build
make docker-run
```

### Production Considerations

- Set `ENVIRONMENT=production` in your environment
- Use a reverse proxy (nginx) for SSL termination
- Set up log aggregation and monitoring
- Configure OpenTelemetry exports to your observability platform

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run quality checks: `make check`
5. Submit a pull request

### Code Quality

This project enforces high code quality standards:

- **Ruff** for linting and formatting
- **MyPy** for static type checking
- **Pre-commit hooks** for automated checks
- **100% type coverage** target

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📝 Notes

- **Authentication & JWT**: The current JWT authentication implementation is for demonstration purposes. Replace with your production authentication system as needed.
- **Dummy Celery Tasks**: Sample tasks in `app/tasks/dummy.py` are provided as examples. Remove and implement your actual background tasks.
- **User Management**: Basic user model and endpoints are included as a starting point. Extend with your application-specific user requirements.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [SQLAlchemy](https://sqlalchemy.org/) for the powerful ORM
- [OpenTelemetry](https://opentelemetry.io/) for observability standards
- [UV](https://github.com/astral-sh/uv) for fast package management
