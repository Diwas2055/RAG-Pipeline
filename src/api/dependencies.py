from celery.result import AsyncResult
from src.core.celery_app import celery_app


def get_task_result(task_id: str) -> AsyncResult:
    return AsyncResult(task_id, app=celery_app)
