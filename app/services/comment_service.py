from fastapi import HTTPException
from app.models.comment import Comment
from app.repos.comment_repo import CommentRepo
from app.repos.news_repo import NewsRepo
from app.repos.user_repo import UserRepo

class CommentService:
    def __init__(self, comments: CommentRepo, news: NewsRepo, users: UserRepo):
        self.comments = comments
        self.news = news
        self.users = users

    async def create(self, data: dict) -> Comment:
        if not await self.news.get(data["news_id"]):
            raise HTTPException(404, "news not found")
        if not await self.users.get(data["author_id"]):
            raise HTTPException(404, "author not found")
        return self.comments.create(data)

    async def update(self, comment_id: int, data: dict) -> Comment:
        comment = await self.comments.get(comment_id)
        if not comment:
            raise HTTPException(404, "comment not found")
        return await self.comments.update(comment_id, data)
