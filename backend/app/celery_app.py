"""
celery_app.py – Celery application instance.
Uses Redis as the broker and result backend (Upstash Redis compatible).
"""
from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "helpdesk",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.ticket_processing",
        "app.tasks.trend_detection",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Task routing
    task_routes={
        "app.tasks.ticket_processing.*": {"queue": "tickets"},
        "app.tasks.trend_detection.*": {"queue": "analytics"},
    },
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Result expiry
    result_expires=3600,  # 1 hour
    # Beat schedule (periodic tasks)
    beat_schedule={
        "detect-trends-hourly": {
            "task": "app.tasks.trend_detection.detect_trends_all_companies",
            "schedule": crontab(minute=0),  # Every hour
        },
    },
)
