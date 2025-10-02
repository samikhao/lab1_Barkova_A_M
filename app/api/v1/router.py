from fastapi import APIRouter
from . import users, news, comments

router = APIRouter(prefix="/api/v1")
router.include_router(users.router, tags=["users"])
router.include_router(news.router, tags=["news"])
router.include_router(comments.router, tags=["comments"])
