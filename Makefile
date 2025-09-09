.PHONY: help install dev-install run dev test lint format type-check clean build docker-build docker-run celery-worker celery-beat celery-flower docs-serve docs-build docs-install

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  dev-install  - Install development dependencies"
	@echo "  run          - Run the FastAPI application"
	@echo "  dev          - Run the FastAPI application in development mode"
	@echo "  test         - Run tests"
	@echo "  lint         - Run ruff linter"
	@echo "  format       - Format code with ruff"
	@echo "  type-check   - Run mypy type checking"
	@echo "  check        - Run all checks (lint, format-check, type-check)"
	@echo "  clean        - Clean up generated files"
	@echo "  build        - Build the application"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"
	@echo "  celery-worker - Start Celery worker (all queues)"
	@echo "  celery-beat  - Start Celery beat scheduler"
	@echo "  celery-flower - Start Flower monitoring UI"
	@echo "  celery-monitor - Show active/scheduled tasks and worker stats"
	@echo "  celery-purge - Purge all tasks from queues"
	@echo "  docs-install - Install documentation dependencies"
	@echo "  docs-serve  - Serve documentation locally for development"
	@echo "  docs-build  - Build documentation for production"


# Installation
install:
	uv sync --no-dev

dev-install:
	uv sync

# Running the application
run:
	fastapi run app/cmd/main.py

dev:
	fastapi dev app/cmd/main.py

# Testing
test:
	PYTHONPATH=. uv run pytest tests/ -v

test-cov:
	PYTHONPATH=. uv run pytest tests/ --cov=app --cov-report=html --cov-report=term --cov-report=xml

# Linting and formatting
lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

# Type checking
type-check:
	uv run mypy app/ --explicit-package-bases

# Combined checks
check: lint format-check type-check
	@echo "All checks passed!"

# Database operations
db-upgrade:
	uv run alembic upgrade head

db-downgrade:
	uv run alembic downgrade -1

db-revision:
	uv run alembic revision --autogenerate -m "$(MESSAGE)"

db-reset:
	uv run alembic downgrade base
	uv run alembic upgrade head

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/

# Development utilities
shell:
	uv run python

# Security scan
security:
	uv run bandit -r app/

# Generate requirements.txt (if needed for deployment)
requirements:
	uv export --no-hashes --format requirements-txt > requirements.txt

requirements-dev:
	uv export --no-hashes --format requirements-txt --group dev > requirements-dev.txt

# Celery commands
celery-beat:
	uv run celery -A app.core.celery_config beat --loglevel=info

celery-flower:
	uv run celery -A app.core.celery_config flower --port=5555

celery-worker-dummy:
	uv run celery -A app.core.celery_config worker -l info -Q fastapi-backend-template -n dummy@%h --pool=solo

celery-monitor:
	@echo "Active tasks:"
	uv run celery -A app.core.celery_config inspect active
	@echo "Scheduled tasks:"
	uv run celery -A app.core.celery_config inspect scheduled
	@echo "Worker stats:"
	uv run celery -A app.core.celery_config inspect stats

celery-purge:
	uv run celery -A app.core.celery_config purge

# Documentation
docs-install:
	uv sync --group docs

docs-serve:
	uv run mkdocs serve

docs-build:
	uv run mkdocs build
