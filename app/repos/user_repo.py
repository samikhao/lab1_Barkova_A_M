from sqlalchemy.orm import Session
from app.models.user import User

class UserRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> User:
        obj = User(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list(self) -> list[User]:
        return self.db.query(User).order_by(User.id).all()

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()
    
    def set_verified(self, user_id: int, value: bool) -> User | None:
        user = self.get(user_id)
        if not user:
            return None
        user.is_verified = value
        self.db.commit()
        self.db.refresh(user)
        return user
