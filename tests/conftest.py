import os
import asyncio
from typing import AsyncGenerator, Any
from sqlalchemy import text

import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CACHE_PREFIX", "test")

from app.api.v1.router import api_router
from app.db.session import get_db
from app.db.base_class import Base
import app.db.base


class FakeRedis:
    def __init__(self):
        self._store: dict[str, Any] = {}

    async def get(self, key: str):
        return self._store.get(key)

    async def setex(self, key: str, ttl: int, value: Any):
        self._store[key] = value

    async def delete(self, key: str):
        self._store.pop(key, None)

    async def scan_iter(self, match: str):
        if match.endswith("*"):
            pref = match[:-1]
            for k in list(self._store.keys()):
                if k.startswith(pref):
                    yield k
        else:
            for k in list(self._store.keys()):
                if k == match:
                    yield k


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    eng = create_async_engine(os.environ["DATABASE_URL"], future=True, echo=False)

    async with eng.begin() as conn:
        await conn.exec_driver_sql("PRAGMA foreign_keys=ON")
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield eng
    await eng.dispose()


@pytest.fixture
async def db(engine) -> AsyncGenerator[AsyncSession, None]:
    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with Session() as session:
        yield session


@pytest.fixture(autouse=True)
async def clean_db(db: AsyncSession):
    await db.execute(text("DELETE FROM comments"))
    await db.execute(text("DELETE FROM news"))
    await db.execute(text("DELETE FROM refresh_sessions"))
    await db.execute(text("DELETE FROM users"))
    await db.commit()
    yield


@pytest.fixture
def fake_redis():
    return FakeRedis()


@pytest.fixture
def app(fake_redis) -> FastAPI:
    test_app = FastAPI(title="test app")
    test_app.include_router(api_router, prefix="/api/v1")

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        raise RuntimeError("db override not set")

    test_app.dependency_overrides[get_db] = _override_get_db

    from app.services import auth_service as auth_svc
    from app.services import news_service as news_svc

    async def _get_redis_override():
        return fake_redis

    auth_svc.get_redis = _get_redis_override
    news_svc.get_redis = _get_redis_override

    class _DummyTask:
        def delay(self, *args, **kwargs):
            return None

    news_svc.send_new_news_notifications = _DummyTask()

    return test_app


@pytest.fixture
async def client(app: FastAPI, db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    from app.db.session import get_db as get_db_dep
    from httpx import ASGITransport, AsyncClient

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db_dep] = _override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def user_factory(db: AsyncSession):
    from app.models.user import User
    from app.core.security import hash_password

    async def _make(
        *,
        email: str,
        name: str = "Test User",
        password: str = "pass1234",
        is_admin: bool = False,
        is_verified_author: bool = False,
    ) -> User:
        u = User(
            email=email,
            name=name,
            password_hash=hash_password(password),
            is_admin=is_admin,
            is_verified_author=is_verified_author,
        )
        db.add(u)
        await db.commit()
        await db.refresh(u)
        return u

    return _make


@pytest.fixture
def token_factory():
    from app.core.security import create_access_token

    def _make(user) -> str:
        return create_access_token(user)

    return _make


@pytest.fixture
async def verified_author(user_factory):
    return await user_factory(email="author@example.com", is_verified_author=True)


@pytest.fixture
async def normal_user(user_factory):
    return await user_factory(email="user@example.com", is_verified_author=False)


@pytest.fixture
async def admin_user(user_factory):
    return await user_factory(
        email="admin@example.com", is_admin=True, is_verified_author=True
    )


@pytest.fixture
def auth_header(token_factory, verified_author):
    token = token_factory(verified_author)
    return {"Authorization": f"Bearer {token}"}
