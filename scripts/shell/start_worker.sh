#!/bin/bash

QUEUE=${1:-default}

echo "Starting Celery worker for queue: $QUEUE"

celery -A src.workers.celery_worker.celery_app worker \
    --loglevel=info \
    --queues=$QUEUE \
    --concurrency=2
