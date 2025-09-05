from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.api.v1 import api_router
from app.core.logger import get_logger
from app.core.settings import settings
from app.core.telemetry import setup_telemetry

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    """Life cycle of the application."""
    logger.info("Starting the application...", operation="lifespan")

    if settings.OTEL_ENABLED:
        setup_telemetry()
        logger.info("Telemetry initialized", operation="lifespan")

    logger.info("Startup complete", operation="lifespan")

    yield

    logger.info("Shutting down...", operation="lifespan")

    logger.info("Shutdown complete", operation="lifespan")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint"""
    return {
        "message": "Welcome to the API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }


FastAPIInstrumentor().instrument_app(app)
