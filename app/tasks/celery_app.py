from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "web_lab1",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "weekly-news-digest": {
        "task": "app.tasks.news_notifications.send_weekly_digest",
        "schedule": crontab(day_of_week="sun", hour=9, minute=0),
    }
}
