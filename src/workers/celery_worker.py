from src.core.celery_app import celery_app
from src.tasks import basic_tasks, document_tasks, vectorstore_tasks, rag_tasks

# Import all tasks to register them with Celery
__all__ = ["celery_app"]
