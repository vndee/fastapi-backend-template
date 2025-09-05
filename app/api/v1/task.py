from fastapi import APIRouter

from app.schemas.task import TaskStatusResponseSchema, TaskTriggerResponseSchema
from app.tasks.dummy import dummy_task, dummy_task_with_tracer

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/dummy")
async def trigger_dummy_task() -> TaskTriggerResponseSchema:
    """Trigger a dummy Celery task"""
    task = dummy_task.delay()
    return TaskTriggerResponseSchema(task_id=task.id, status="Task queued successfully")


@router.post("/dummy-with-tracer")
async def trigger_dummy_task_with_tracer() -> TaskTriggerResponseSchema:
    """Trigger a dummy Celery task with tracer"""
    task = dummy_task_with_tracer.delay()
    return TaskTriggerResponseSchema(task_id=task.id, status="Task queued successfully")


@router.get("/status/{task_id}")
async def get_task_status(task_id: str) -> TaskStatusResponseSchema:
    """Get the status of a task"""
    from app.core.celery_config import celery_app

    result = celery_app.AsyncResult(task_id)
    return TaskStatusResponseSchema(
        task_id=task_id,
        status=result.status,
        result=str(result.result) if result.result else None,
    )
