from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_TITLE: str = "web lab1"

    DATABASE_URL: str
    
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TTL_MIN: int = 15
    REFRESH_TTL_DAYS: int = 14

    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None
    GITHUB_REDIRECT_URL: str | None = None

    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_PREFIX: str = "app"
    CACHE_TTL_NEWS: int = 300
    USER_CACHE_TTL_MIN: int = 20

    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    NOTIFICATIONS_LOG_FILE: str = "notifications.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

if settings.CELERY_BROKER_URL is None:
    settings.CELERY_BROKER_URL = settings.REDIS_URL

if settings.CELERY_RESULT_BACKEND is None:
    settings.CELERY_RESULT_BACKEND = settings.REDIS_URL
