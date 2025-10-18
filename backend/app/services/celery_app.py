"""Celery application configuration for background tasks."""

from celery import Celery
from app.core.config import get_settings

settings = get_settings()

# Initialize Celery app
celery_app = Celery(
    "sprintforge",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['app.tasks.notification_tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Optional: Task routes for better organization
celery_app.conf.task_routes = {
    'app.tasks.notification_tasks.*': {'queue': 'notifications'},
}
