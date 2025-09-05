from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.codes import ResponseCode
from app.core.database import get_db
from app.core.exceptions import APIException
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])


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
