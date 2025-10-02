from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    name: str
    email: EmailStr
    avatar_url: str | None = None


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: int
    registered_at: datetime
    is_verified: bool

    class Config:
        # для распознавания ORM-объекта pydantic'ом
        from_attributes = True
