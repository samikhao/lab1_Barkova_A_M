from sqlalchemy.orm import Session
from app.models.news import News

class NewsRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> News:
        obj = News(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list(self) -> list[News]:
        return self.db.query(News).order_by(News.id).all()

    def get(self, news_id: int) -> News | None:
        return self.db.get(News, news_id)

    def update(self, news_id: int, data: dict) -> News:
        obj = self.db.get(News, news_id)
        for k, v in data.items():
            setattr(obj, k, v)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, news_id: int) -> None:
        obj = self.db.get(News, news_id)
        self.db.delete(obj)
        self.db.commit()
