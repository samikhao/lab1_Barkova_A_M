from fastapi import APIRouter

from app.api.v1.users import router as users_router
from app.api.v1.news import router as news_router
from app.api.v1.comments import router as comments_router

api_router = APIRouter()
api_router.include_router(users_router)
api_router.include_router(news_router)
api_router.include_router(comments_router) 
