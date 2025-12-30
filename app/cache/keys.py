from app.core.config import settings


PREFIX = settings.CACHE_PREFIX


def news_all() -> str:
    return f"{PREFIX}:news:all"


def news_id(news_id: int) -> str:
    return f"{PREFIX}:news:id:{news_id}"


def user_id(user_id: int) -> str:
    return f"{PREFIX}:user:id:{user_id}"


def session(refresh_hash: str) -> str:
    return f"{PREFIX}:session:{refresh_hash}"
