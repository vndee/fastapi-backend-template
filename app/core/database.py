import logging
from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool

from app.core.settings import settings

logger = logging.getLogger(__name__)


def _get_engine_config() -> dict[str, Any]:
    """Get database engine configuration based on database type."""
    config: dict[str, Any] = {
        "echo": settings.DB_ECHO,
        "future": True,
    }

    if "sqlite" in settings.DATABASE_URL:
        config.update(
            {
                "poolclass": StaticPool,
                "connect_args": {"check_same_thread": False},
            }
        )
    else:
        pool_config = settings.database_pool_config
        config.update(
            {
                "poolclass": QueuePool,
                **pool_config,
                "connect_args": {
                    "connect_timeout": settings.DB_CONNECT_TIMEOUT,
                    "server_settings": {
                        "application_name": settings.APP_NAME,
                        "jit": "off",  # Disable JIT for simple queries
                    },
                },
            }
        )

    return config


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    """Set SQLite pragmas for better performance and reliability."""
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=1000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


@event.listens_for(Engine, "connect")
def _ping_connection(dbapi_connection: Any, connection_record: Any) -> None:
    """Ensure connections are alive before use."""
    try:
        # Use the raw DBAPI connection to avoid SQLAlchemy transaction issues
        cursor = dbapi_connection.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
    except Exception:
        logger.warning("Database connection lost, invalidating connection")
        connection_record.invalidate()
        raise


def create_database_engine() -> Engine:
    """Create and configure the database engine."""
    try:
        config = _get_engine_config()
        engine = create_engine(settings.DATABASE_URL, **config)

        logger.info(
            f"Database engine created successfully for {settings.DATABASE_URL.split('@')[-1]}"
        )
        return engine

    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise


engine = create_database_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()


def get_db() -> Generator[Session, Any, None]:
    """Get database session with proper error handling."""
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, Any, None]:
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database transaction failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def check_db_health() -> bool:
    """Check database connectivity and health."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return bool(result.scalar() == 1)
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def get_db_info() -> dict[str, Any]:
    """Get database information for monitoring."""
    try:
        pool_info = {}
        if hasattr(engine.pool, "size"):
            pool_info["pool_size"] = engine.pool.size()
        if hasattr(engine.pool, "checkedin"):
            pool_info["checked_in"] = engine.pool.checkedin()
        if hasattr(engine.pool, "checkedout"):
            pool_info["checked_out"] = engine.pool.checkedout()
        if hasattr(engine.pool, "overflow"):
            pool_info["overflow"] = engine.pool.overflow()

        return {
            "url": settings.DATABASE_URL.split("@")[-1]
            if "@" in settings.DATABASE_URL
            else settings.DATABASE_URL,
            "driver": engine.driver,
            "pool_info": pool_info,
            "echo": settings.DB_ECHO,
        }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {"error": str(e)}
