import os

from dotenv import load_dotenv
load_dotenv()

class Settings:
    APP_TITLE: str = "web lab1"
    DATABASE_URL: str = os.getenv("DATABASE_URL")

settings = Settings()
