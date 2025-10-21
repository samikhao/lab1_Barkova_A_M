from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TypedDict

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import jwt

from app.core.config import settings
from app.models.user import User


_ph = PasswordHasher()

def hash_password(password: str) -> str:
    return _ph.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False


class TokenPayload(TypedDict):
    sub: str
    uid: int
    is_admin: bool
    is_verified_author: bool
    exp: int

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _exp_minutes(minutes: int) -> datetime:
    return _now() + timedelta(minutes=minutes)

def _exp_days(days: int) -> datetime:
    return _now() + timedelta(days=days)


def create_access_token(user: User) -> str:
    exp = _exp_minutes(settings.ACCESS_TTL_MIN)
    payload: TokenPayload = {
        "sub": str(user.email),
        "uid": int(user.id),
        "is_admin": bool(user.is_admin),
        "is_verified_author": bool(getattr(user, "is_verified_author", False)),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> TokenPayload:
    data = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    payload: TokenPayload = {
        "sub": str(data.get("sub", "")),
        "uid": int(data.get("uid", 0)),
        "is_admin": bool(data.get("is_admin", False)),
        "is_verified_author": bool(data.get("is_verified_author", False)),
        "exp": int(data.get("exp", 0)),
    }
    return payload


def create_refresh_token(user: User) -> tuple[str, datetime]:
    exp = _exp_days(settings.REFRESH_TTL_DAYS)
    payload: TokenPayload = {
        "sub": str(user.email),
        "uid": int(user.id),
        "is_admin": bool(user.is_admin),
        "is_verified_author": bool(getattr(user, "is_verified_author", False)),
        "exp": int(exp.timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, exp
