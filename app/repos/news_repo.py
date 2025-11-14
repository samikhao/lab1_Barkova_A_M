from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.news import News

class NewsRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> News:
        obj = News(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def list(self) -> list[News]:
        res = await self.db.scalars(select(News).order_by(News.id))
        return res.all()

    async def list_since(self, dt_from: datetime) -> list[News]:
        res = await self.db.scalars(
            select(News)
            .where(News.published_at >= dt_from)
            .order_by(News.published_at)
        )
        return res.all()

    async def get(self, news_id: int) -> News | None:
        return await self.db.get(News, news_id)

    async def update(self, news_id: int, data: dict) -> News:
        obj = await self.db.get(News, news_id)
        for k, v in data.items():
            setattr(obj, k, v)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, news_id: int) -> None:
        obj = await self.db.get(News, news_id)
        await self.db.delete(obj)
        await self.db.commit()
