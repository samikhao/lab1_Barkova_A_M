from sqlalchemy.orm import Session
from app.models.comment import Comment

class CommentRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> Comment:
        obj = Comment(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list(self) -> list[Comment]:
        return self.db.query(Comment).order_by(Comment.id).all()

    def get(self, comment_id: int) -> Comment | None:
        return self.db.get(Comment, comment_id)

    def update(self, comment_id: int, data: dict) -> Comment:
        obj = self.db.get(Comment, comment_id)
        if "text" in data and data["text"] is not None:
            obj.text = data["text"]
        self.db.commit()
        self.db.refresh(obj)
        return obj
