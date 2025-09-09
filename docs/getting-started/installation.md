# Installation

This guide will help you set up the FastAPI Backend Template on your local development environment.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.11+** - The application requires Python 3.11 or higher
- **PostgreSQL** - For the primary database
- **Redis** - For caching and session storage
- **UV** - Ultra-fast Python package manager (recommended)
- **Docker** (optional) - For running services via containers

### Installing UV

UV is the recommended package manager for this project. Install it using:

=== "macOS/Linux"
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows"
    ```powershell
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

=== "Alternative (pip)"
    ```bash
    pip install uv
    ```

## Project Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fastapi-backend-template
```

### 2. Install Dependencies

Install all dependencies including development tools:

```bash
make dev-install
```

This command will:

- Create a virtual environment
- Install all project dependencies
- Install development dependencies (linting, testing, etc.)
- Install pre-commit hooks

### 3. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration. See [Configuration](configuration.md) for detailed settings.

### 4. Start Services

#### Option A: Using Docker (Recommended)

Start PostgreSQL and Redis using Docker Compose:

```bash
docker-compose up -d postgres redis
```

#### Option B: Local Installation

If you prefer to run services locally, ensure PostgreSQL and Redis are installed and running on your system.

### 5. Database Setup

Run database migrations:

```bash
make db-upgrade
```

### 6. Verify Installation

Start the development server:

```bash
make dev
```

The API should now be available at:

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Next Steps

Once installation is complete, proceed to:

1. [Configuration](configuration.md) - Learn about environment variables and settings
2. [Quick Start](quick-start.md) - Get familiar with the application structure
3. [Development Guide](../development/environment.md) - Set up your development workflow

## Troubleshooting

### Common Issues

**UV not found**
```bash
# Ensure UV is in your PATH
echo $PATH
# Restart your terminal after installation
```

**Database connection errors**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres
# Or for local installation
pg_isready -h localhost -p 5432
```

**Redis connection errors**
```bash
# Check if Redis is running
docker-compose ps redis
# Or for local installation
redis-cli ping
```

**Permission errors during installation**
```bash
# On macOS/Linux, you might need to adjust permissions
sudo chown -R $(whoami) ~/.local/share/uv
```

For more issues, please check the project's issue tracker or create a new issue.
