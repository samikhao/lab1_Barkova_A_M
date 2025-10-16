from pydantic import BaseSettings


class Settings(BaseSettings):
    APP_TITLE: str = "web lab1"
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TTL_MIN: int = 15
    REFRESH_TTL_DAYS: int = 14

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
