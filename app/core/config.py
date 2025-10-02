import os

class Settings:
    APP_TITLE: str = "web lab1"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/lab1",
    )

settings = Settings()
