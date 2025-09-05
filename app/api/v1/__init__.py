from fastapi import APIRouter

from app.api.v1 import auth, health, task, users

api_router = APIRouter(prefix="/v1")


api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(task.router)

__all__ = ["api_router"]
