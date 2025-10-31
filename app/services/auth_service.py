from __future__ import annotations

import hashlib
import logging
from typing import Any
from datetime import datetime, timezone

from fastapi import HTTPException, Request
from jose import JWTError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User
from app.models.refresh_session import RefreshSession
from app.repos.user_repo import UserRepo
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenPair, RefreshRequest, LogoutRequest, SessionPublic
)

from app.cache.redis_client import get_redis
from app.cache.codec import encode, decode
from app.cache import keys


logger = logging.getLogger("cache.auth")

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _from_iso(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hash_to_int(h: str) -> int:
    try:
        return int(h[:8], 16)
    except Exception:
        return 0


def _refresh_ttl_seconds() -> int:
    return int(settings.REFRESH_TTL_DAYS) * 24 * 60 * 60

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepo(db)

    async def _rs_create(self, *, user_id: int, token: str, ua: str | None, ip: str | None, expires_at: datetime):
        r = await get_redis()
        h = _sha256(token)
        key = keys.session(h)
        value: dict[str, Any] = {
            "hash": h,
            "user_id": user_id,
            "user_agent": ua,
            "ip": ip,
            "created_at": _to_iso(_now()),
            "expires_at": _to_iso(expires_at),
        }
        await r.setex(key, _refresh_ttl_seconds(), encode(value))
        logger.info("session SET: %s", key)
        return value

    async def _rs_find_active(self, token: str) -> dict[str, Any] | None:
        r = await get_redis()
        h = _sha256(token)
        key = keys.session(h)
        data = decode(await r.get(key))
        if not data:
            logger.info("session MISS: %s", key)
            return None
        try:
            exp = _from_iso(data["expires_at"])
            if exp <= _now():
                logger.info("session EXPIRED: %s", key)
                return None
        except Exception:
            logger.info("session CORRUPT: %s", key)
            return None
        logger.info("session HIT: %s", key)
        return data

    async def _rs_revoke(self, token: str) -> None:
        r = await get_redis()
        h = _sha256(token)
        key = keys.session(h)
        await r.delete(key)
        logger.info("session DEL: %s", key)

    async def _rs_list_for_user(self, user_id: int) -> list[dict[str, Any]]:
        r = await get_redis()
        pattern = f"{settings.CACHE_PREFIX}:session:*"
        result: list[dict[str, Any]] = []
        async for key in r.scan_iter(match=pattern):
            data = decode(await r.get(key))
            if not data:
                continue
            if int(data.get("user_id", -1)) != int(user_id):
                continue
            result.append(data)
        return result

    @staticmethod
    def _ua_ip(request: Request) -> tuple[str | None, str | None]:
        ua = request.headers.get("User-Agent")
        ip = request.client.host if request.client else None
        return ua, ip

    async def _issue_tokens(self, user: User, request: Request) -> TokenPair:
        access = create_access_token(user)
        refresh, exp_dt = create_refresh_token(user)
        ua, ip = self._ua_ip(request)
        await self._rs_create(user_id=user.id, token=refresh, ua=ua, ip=ip, expires_at=exp_dt)
        return TokenPair(access=access, refresh=refresh)

    async def register(self, req: RegisterRequest, request: Request) -> TokenPair:
        exists = await self.users.get_by_email(req.email)
        if exists:
            raise HTTPException(status_code=409, detail="Email already registered")
        user = await self.users.create({
            "name": req.name,
            "email": req.email,
            "password_hash": hash_password(req.password),
        })
        return await self._issue_tokens(user, request)

    async def login_password(self, req: LoginRequest, request: Request) -> TokenPair:
        user = await self.users.get_by_email(req.email)
        if not user or not user.password_hash or not verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return await self._issue_tokens(user, request)

    async def refresh(self, req: RefreshRequest, request: Request) -> TokenPair:
        try:
            payload = decode_token(req.refresh)
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        sess = await self._rs_find_active(req.refresh)

        try:
            expires_at = _from_iso(sess["expires_at"])
        except Exception:
            await self._rs_revoke(req.refresh)
            raise HTTPException(status_code=401, detail="Corrupted session data")
        
        if expires_at <= datetime.now(timezone.utc):
            await self._rs_revoke(req.refresh)
            raise HTTPException(status_code=401, detail="Refresh session expired")

        user = await self.db.get(User, payload["uid"])
        if not user:
            await self._rs_revoke(req.refresh)
            raise HTTPException(status_code=401, detail="User not found")

        await self._rs_revoke(req.refresh)
        return await self._issue_tokens(user, request)

    async def logout(self, req: LogoutRequest) -> None:
        await self._rs_revoke(req.refresh)

    async def list_sessions(self, user: User) -> list[SessionPublic]:
        """
        Возвращаем список активных refresh-сессий из Redis.
        Поле id синтетическое (по хэшу), revoked всегда False (ключ существует).
        """
        rows = await self._rs_list_for_user(user.id)
        out: list[SessionPublic] = []
        for r in rows:
            try:
                created = _from_iso(r["created_at"])
                expires = _from_iso(r["expires_at"])
                sid = _hash_to_int(r["hash"])
                out.append(SessionPublic(
                    id=sid,
                    user_agent=r.get("user_agent"),
                    ip=r.get("ip"),
                    created_at=created,
                    expires_at=expires,
                    revoked=False,
                ))
            except Exception:
                continue
        out.sort(key=lambda x: x.created_at, reverse=True)
        return out

    async def github_callback(self, request: Request, sso) -> TokenPair:
        async with sso:
            gh_user = await sso.verify_and_process(request)
        if not gh_user:
            raise HTTPException(status_code=401, detail="GitHub auth failed")

        user = await self.db.scalar(select(User).where(User.github_id == str(gh_user.id)))

        if not user and gh_user.email:
            user = await self.users.get_by_email(gh_user.email)
            if user:
                user.github_id = str(gh_user.id)
                if gh_user.picture and not user.avatar_url:
                    user.avatar_url = gh_user.picture
                await self.db.commit()
                await self.db.refresh(user)

        if not user:
            user = await self.users.create({
                "name": gh_user.display_name or "GitHub User",
                "email": gh_user.email or f"gh_{gh_user.id}@example.com",
                "github_id": str(gh_user.id),
                "avatar_url": gh_user.picture,
            })

        return await self._issue_tokens(user, request)

    async def github_login(self, sso):
        return await sso.get_login_redirect()
