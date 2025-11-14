import asyncio
import logging
from datetime import datetime, timedelta, timezone

from celery import Task
from celery.utils.log import get_task_logger
from redis import Redis

from app.core.config import settings
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.repos.user_repo import UserRepo
from app.repos.news_repo import NewsRepo


logger = get_task_logger(__name__)

file_handler = logging.FileHandler(settings.NOTIFICATIONS_LOG_FILE)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


def get_redis_sync() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)


async def _get_users_and_news(news_id: int):
    async with SessionLocal() as db:
        users = await UserRepo(db).list()
        news = await NewsRepo(db).get(news_id)
        return users, news


async def _get_users_and_weekly_news():
    async with SessionLocal() as db:
        users = await UserRepo(db).list()
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        news_repo = NewsRepo(db)
        news_items = await news_repo.list_since(week_ago)
        return users, news_items, now


class BaseRetryTask(Task):
    autoretry_for = (Exception,)
    max_retries = 5
    retry_backoff = True
    retry_backoff_max = 3600
    retry_jitter = True


@celery_app.task(
    base=BaseRetryTask,
    name="app.tasks.news_notifications.send_new_news_notifications",
)
def send_new_news_notifications(news_id: int):
    redis = get_redis_sync()

    users, news = asyncio.run(_get_users_and_news(news_id))

    if news is None:
        logger.warning("News %s not found, skip notifications", news_id)
        return

    for user in users:
        key = f"notify:news:{news.id}:user:{user.id}"

        was_set = redis.setnx(key, datetime.now(timezone.utc).isoformat())
        if not was_set:
            continue

        redis.expire(key, 60 * 60 * 24 * 30)

        logger.info(
            "[NEW_NEWS] to=%s <%s> news_id=%s title=%r",
            user.name,
            user.email,
            news.id,
            news.title,
        )


@celery_app.task(
    base=BaseRetryTask,
    name="app.tasks.news_notifications.send_weekly_digest",
)
def send_weekly_digest():
    redis = get_redis_sync()

    users, news_items, now = asyncio.run(_get_users_and_weekly_news())

    if not news_items:
        logger.info("[WEEKLY_DIGEST] no news in last 7 days, skip")
        return

    iso_year, iso_week, _ = now.isocalendar()

    news_ids = [n.id for n in news_items]
    titles = [n.title for n in news_items]

    for user in users:
        key = f"digest:{iso_year}:{iso_week}:user:{user.id}"

        was_set = redis.setnx(key, now.isoformat())
        if not was_set:
            continue

        redis.expire(key, 60 * 60 * 24 * 30)

        logger.info(
            "[WEEKLY_DIGEST] to=%s <%s> week=%s-%s news_ids=%s titles=%s",
            user.name,
            user.email,
            iso_year,
            iso_week,
            news_ids,
            titles,
        )
