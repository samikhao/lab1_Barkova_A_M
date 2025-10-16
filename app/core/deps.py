from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repos.user_repo import UserRepo
from app.repos.news_repo import NewsRepo
from app.repos.comment_repo import CommentRepo

from app.models.user import User
from app.models.news import News
from app.models.comment import Comment
from app.core.security import decode_token

def get_repos(db: Session = Depends(get_db)):
    return {
        "users": UserRepo(db),
        "news": NewsRepo(db),
        "comments": CommentRepo(db),
    }


def _bearer(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return auth.split(" ", 1)[1]


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    payload = decode_token(_bearer(request))
    user = db.query(User).get(payload["uid"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def resolve_news(news_id: int, db: Session = Depends(get_db)) -> News:
    news = db.query(News).get(news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news


def resolve_comment(comment_id: int, db: Session = Depends(get_db)) -> Comment:
    comment = db.query(Comment).get(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


def require_authenticated(user: User = Depends(get_current_user)) -> User:
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return user


def require_author_verified(user: User = Depends(get_current_user)) -> User:
    if not (user.is_verified_author or user.is_admin):
        raise HTTPException(status_code=403, detail="Author verification required")
    return user


def require_news_owner_or_admin(
    news: News = Depends(resolve_news),
    user: User = Depends(get_current_user),
) -> News:
    if not (user.is_admin or news.author_id == user.id):
        raise HTTPException(status_code=403, detail="Not allowed for this news")
    return news


def require_comment_owner_or_admin(
    comment: Comment = Depends(resolve_comment),
    user: User = Depends(get_current_user),
) -> Comment:
    if not (user.is_admin or comment.author_id == user.id):
        raise HTTPException(status_code=403, detail="Not allowed for this comment")
    return comment
