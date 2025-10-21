from fastapi import HTTPException
from app.models.user import User
from app.models.news import News
from app.repos.user_repo import UserRepo
from app.repos.news_repo import NewsRepo

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
        return await self.news.create(data)

    async def update(self, news_id: int, data: dict) -> News:
        news = await self.news.get(news_id)
        if not news:
            raise HTTPException(404, "news not found")
        return await self.news.update(news_id, data)

    async def delete(self, news_id: int) -> None:
        news = await self.news.get(news_id)
        if not news:
            raise HTTPException(404, "news not found")
        await self.news.delete(news_id)
