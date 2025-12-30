from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repos.user_repo import UserRepo
from app.cache.redis_client import get_redis
from app.cache.codec import encode, decode

import logging

logger = logging.getLogger(__name__)

CACHE_TTL_USER = 300


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepo(db)

    async def create_user(self, data: dict):
        if await self.repo.get_by_email(data["email"]):
            raise HTTPException(status_code=409, detail="Email already exists")

        user = await self.repo.create(data)
        logger.info("user created: %s", user.email)
        return user

    async def list_users(self):
        return await self.repo.list()

    async def set_verified(self, user_id: int, value: bool):
        user = await self.repo.set_verified(user_id, value)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        redis = await get_redis()
        key = f"app:user:{user_id}"
        await redis.delete(key)
        logger.info("user cache DEL: %s", key)
        return user

    @staticmethod
    async def get_user_roles_fast(db: AsyncSession, user_id: int) -> dict[str, bool]:
        redis = await get_redis()
        key = f"app:user:{user_id}"

        cached = decode(await redis.get(key))
        if cached:
            logger.info("user cache HIT: %s", key)
            return cached

        logger.info("user cache MISS: %s", key)

        repo = UserRepo(db)
        user = await repo.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        data = {
            "id": user.id,
            "is_admin": bool(user.is_admin),
            "is_verified_author": bool(user.is_verified_author),
        }

        await redis.setex(key, CACHE_TTL_USER, encode(data))
        logger.info("user cache SET: %s", key)
        return data
