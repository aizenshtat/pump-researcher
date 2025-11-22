"""Celery application configuration."""

from celery import Celery
import os

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "pump_researcher",
    broker=redis_url,
    backend=redis_url,
    include=["src.worker.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=900,  # 15 minutes max
    worker_prefetch_multiplier=1,
    worker_concurrency=2,
)

# Schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "run-pump-detection-hourly": {
        "task": "src.worker.tasks.run_pump_agent_scheduled",
        "schedule": 3600.0,  # Every hour
    },
}
