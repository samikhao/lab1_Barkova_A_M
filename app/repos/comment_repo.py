from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.comment import Comment

class CommentRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> Comment:
        obj = Comment(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def list(self) -> list[Comment]:
        res = await self.db.scalars(select(Comment).order_by(Comment.id))
        return res.all()

    async def get(self, comment_id: int) -> Comment | None:
        return await self.db.get(Comment, comment_id)

    async def update(self, comment_id: int, data: dict) -> Comment:
        obj = await self.db.get(Comment, comment_id)
        if "text" in data and data["text"] is not None:
            obj.text = data["text"]
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, comment_id: int) -> None:
        obj = await self.db.get(Comment, comment_id)
        if not obj:
            return
        await self.db.delete(obj)
        await self.db.commit()
