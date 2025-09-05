"""Dummy task to test the Celery worker"""

from app.core.celery_config import celery_app
from app.core.logger import get_logger
from app.core.telemetry import get_tracer
from app.tasks.base import BaseTaskWithDatabaseContext

logger = get_logger(__name__)
tracer = get_tracer(__name__)


@celery_app.task(name="dummy_task", bind=True, base=BaseTaskWithDatabaseContext)
def dummy_task(self: BaseTaskWithDatabaseContext) -> None:
    """Dummy task to test the Celery worker"""
    logger.info("This is a dummy task", operation="dummy_task")
    # You can do something with database here
    # from app.repositories.user import UserRepository
    # from app.schemas.user import UserCreateSchema
    # from app.services.user import UserService

    # user_service = UserService(UserRepository(self.db))
    # user_service.create(
    #     UserCreateSchema(email="test@test.com", username="test", password="Test@1234")
    # )

    # Or perform some other task...
    # Like printing a string
    print("This is a dummy task")


@celery_app.task(
    name="dummy_task_with_tracer", bind=True, base=BaseTaskWithDatabaseContext
)
@tracer.start_as_current_span("dummy_task_with_tracer")
def dummy_task_with_tracer(self: BaseTaskWithDatabaseContext) -> None:
    """Dummy task to test the Celery worker with tracer"""
    logger.info("This is a dummy task with tracer", operation="dummy_task_with_tracer")
    print("This is a dummy task with tracer")
