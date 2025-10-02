from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.repos.user_repo import UserRepo
from app.repos.news_repo import NewsRepo
from app.repos.comment_repo import CommentRepo

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repos(db: Session = Depends(get_db)):
    return {
        "users": UserRepo(db),
        "news": NewsRepo(db),
        "comments": CommentRepo(db),
    }
