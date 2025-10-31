from fastapi import HTTPException
from app.models.user import User
from app.models.news import News
from app.schemas.news import NewsRead
from app.repos.user_repo import UserRepo
from app.repos.news_repo import NewsRepo
from app.cache.redis_client import get_redis
from app.cache.codec import encode, decode
from app.cache import keys
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class NewsService:
    def __init__(self, users: UserRepo, news: NewsRepo):
        self.users = users
        self.news = news

    async def create(self, data: dict) -> News:
        author: User | None = await self.users.get(data["author_id"])
        if not author:
            raise HTTPException(404, "author not found")
        if not author.is_verified_author:
            raise HTTPException(403, "author is not verified to publish news")
        
        news = await self.news.create(data)

        redis = await get_redis()
        await redis.delete(keys.news_all())
        await redis.delete(keys.news_id(news.id))
        logger.info("cache DEL (create): %s", news.id)

        return news

    async def update(self, news_id: int, data: dict) -> News:
        news = await self.news.get(news_id)
        if not news:
            raise HTTPException(404, "news not found")
        
        news = await self.news.update(news_id, data)

        redis = await get_redis()
        await redis.delete(keys.news_all())
        await redis.delete(keys.news_id(news_id))
        logger.info("cache DEL (update): %s", news_id)

        return news

    async def delete(self, news_id: int) -> None:
        news = await self.news.get(news_id)
        if not news:
            raise HTTPException(404, "news not found")
        
        news = await self.news.delete(news_id)

        redis = await get_redis()
        await redis.delete(keys.news_all())
        await redis.delete(keys.news_id(news_id))
        logger.info("cache DEL (delete): %s", news_id)

    async def list_cached(self) -> list[News]:
        """
        Read-through кэш списка новостей.
        """
        redis = await get_redis()
        key = keys.news_all()

        cached = decode(await redis.get(key))
        if cached:
            logger.info("cache HIT: %s", key)
            return cached

        logger.info("cache MISS: %s", key)
        data = await self.news.list()
        payload = [NewsRead.model_validate(n).model_dump() for n in data]
        await redis.setex(key, settings.CACHE_TTL_NEWS, encode(payload))
        logger.info("cache SET: %s", key)
        return data
