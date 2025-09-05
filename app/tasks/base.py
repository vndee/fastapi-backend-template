import gc
from typing import Any

from celery import Task  # type:ignore[import-untyped]

from app.core.database import get_db_context


class BaseTaskWithDatabaseContext(Task):
    """Base task class that provides database session."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        try:
            with get_db_context() as db:
                self.db = db
                result = super().__call__(*args, **kwargs)
                # Force garbage collection after each task
                gc.collect()
                return result
        except Exception:
            # Ensure cleanup even on error
            gc.collect()
            raise
