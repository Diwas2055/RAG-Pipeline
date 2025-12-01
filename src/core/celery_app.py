from celery import Celery
from src.core.config import get_settings
from src.core.queues import TASK_ROUTES

settings = get_settings()

celery_app = Celery(
    "rag_pipeline",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=settings.celery_accept_content,
    timezone=settings.celery_timezone,
    enable_utc=settings.celery_enable_utc,
    result_expires=settings.celery_result_expires,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_routes=TASK_ROUTES,
)
