import redis.asyncio as redis
from app.core.config import settings


redis_client: redis.Redis | None = None


async def init_redis() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=False,
            encoding="utf-8",
            health_check_interval=30,
        )
    return redis_client


async def get_redis() -> redis.Redis:
    if redis_client is None:
        await init_redis()
    return redis_client
