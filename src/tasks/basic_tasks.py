import time
import logging
from src.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.process_data")
def process_data_task(data: str):
    time.sleep(20)
    return f"Processed: {data}"


@celery_app.task(name="tasks.add_numbers")
def add_numbers_task(x: int, y: int):
    return x + y


@celery_app.task(name="tasks.divide_numbers", bind=True, max_retries=5)
def divide_numbers_task(self, x: int, y: int):
    try:
        if y == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return x / y
    except ZeroDivisionError as exc:
        logger.warning(
            f"Retrying division for task {self.request.id} "
            f"on attempt {self.request.retries + 1}/{self.max_retries}"
        )
        countdown = 2**self.request.retries
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(name="tasks.aggregate_results")
def aggregate_results_task(results: list):
    return sum(results)
