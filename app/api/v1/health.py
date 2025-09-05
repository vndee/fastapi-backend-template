from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.codes import ResponseCode
from app.core.database import engine, get_db, get_db_info
from app.core.exceptions import APIException
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/readiness", status_code=status.HTTP_200_OK)
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Kubernetes readiness probe endpoint.
    """
    result = db.execute(text("SELECT 1"))
    if result.scalar() != 1:  # type: ignore[attr-defined]
        raise APIException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message="Database connection failed",
            error_code=ResponseCode.SERVICE_UNAVAILABLE,
        )
    logger.info("Database connection successful", operation="readiness_check")

    return {
        "status": "ready",
        "timestamp": datetime.now().isoformat(),
        "checks": {"database": "ready"},
    }


@router.get("/liveness", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes liveness probe endpoint.
    """
    return {"status": "alive", "timestamp": datetime.now().isoformat()}


@router.get("/db-pool", status_code=status.HTTP_200_OK)
async def database_pool_status() -> Dict[str, Any]:
    """
    Database connection pool monitoring endpoint.
    Provides insights into connection pool health and usage.
    """
    try:
        pool = engine.pool

        # Safely get pool metrics with proper type checking
        pool_size = getattr(pool, "size", lambda: 0)()
        checked_in = getattr(pool, "checkedin", lambda: 0)()
        checked_out = getattr(pool, "checkedout", lambda: 0)()
        overflow = getattr(pool, "overflow", lambda: 0)()
        total_connections = pool_size + overflow

        # Calculate utilization with division by zero protection
        utilization_percent = 0.0
        if total_connections > 0:
            utilization_percent = round((checked_out / total_connections) * 100, 2)

        pool_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "pool_metrics": {
                "pool_size": pool_size,
                "checked_in": checked_in,
                "checked_out": checked_out,
                "overflow": overflow,
                "total_connections": total_connections,
            },
            "pool_utilization": {
                "utilization_percent": utilization_percent,
                "available_connections": max(0, total_connections - checked_out),
            },
            "database_info": get_db_info(),
        }

        # Add warning if utilization is high
        if utilization_percent > 80:
            pool_status["warnings"] = ["High connection pool utilization"]

        return pool_status

    except Exception as e:
        logger.error(
            f"Failed to get pool status: {e}", operation="database_pool_status"
        )
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve database pool status",
            error_code=ResponseCode.INTERNAL_SERVER_ERROR,
        )
