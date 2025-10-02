import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    content: Mapped[dict | list | None] = mapped_column(JSON)
    published_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now(datetime.timezone.utc), nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String(500))

    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    author = relationship("User", back_populates="news")

    comments = relationship("Comment", back_populates="news", cascade="all, delete-orphan")
