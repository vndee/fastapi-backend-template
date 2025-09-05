from typing import Optional

from pydantic import BaseModel


class TaskTriggerResponseSchema(BaseModel):
    task_id: str
    status: str


class TaskStatusResponseSchema(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None
