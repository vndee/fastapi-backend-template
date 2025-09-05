from celery import Celery  # type:ignore[import-untyped]

from app.core.settings import settings


def create_celery_app() -> Celery:
    """Create a Celery app instance."""
    app = Celery(
        "fastapi-backend-template",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL,
        include=["app.tasks.logging_tasks"],
    )

    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,
        task_soft_time_limit=3600,
        worker_prefetch_multiplier=1,
        task_routes={
            "logging_tasks.log_api_key_usage": {"queue": "fastapi-backend-template"},
        },
        task_default_queue="default",
        task_default_exchange="default",
        task_default_exchange_type="direct",
        task_default_routing_key="default",
    )
    return app


celery_app = create_celery_app()
