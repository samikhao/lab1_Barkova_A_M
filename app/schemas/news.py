from datetime import datetime
from typing import Any
from pydantic import BaseModel


class NewsBase(BaseModel):
    title: str
    content: Any | None = None
    cover_url: str | None = None


class NewsCreate(NewsBase):
    pass


class NewsUpdate(BaseModel):
    title: str | None = None
    content: Any | None = None
    cover_url: str | None = None


class NewsRead(NewsBase):
    id: int
    published_at: datetime
    author_id: int

    class Config:
        # для распознавания ORM-объекта pydantic'ом
        from_attributes = True
