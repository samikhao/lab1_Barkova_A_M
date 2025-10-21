from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

class UserRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> User:
        obj = User(**data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def list(self) -> list[User]:
        res = await self.db.scalars(select(User).order_by(User.id))
        return res.all()

    async def get(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self.db.scalar(select(User).where(User.email == email))
    
    async def set_verified(self, user_id: int, value: bool) -> User | None:
        user = await self.get(user_id)
        if not user:
            return None
        user.is_verified_author = value
        await self.db.commit()
        await self.db.refresh(user)
        return user
