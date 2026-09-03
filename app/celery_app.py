# app/celery_app.py

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "insurance_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True
)

celery_app.conf.beat_schedule = {
    "daily-premium-and-policy-checks": {
        "task": "app.tasks.run_daily_premium_and_policy_checks",
        "schedule": crontab(hour=7, minute=0)
    }
}