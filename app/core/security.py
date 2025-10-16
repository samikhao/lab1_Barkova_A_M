from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TypedDict, Tuple

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.refresh_session import RefreshSession


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


def create_refresh_session(db: Session, user: User, user_agent: str | None, ip: str | None) -> str:
    exp_dt = _exp_days(settings.REFRESH_TTL_DAYS)
    payload: TokenPayload = {
        "sub": str(user.email),
        "uid": int(user.id),
        "is_admin": bool(user.is_admin),
        "is_verified_author": bool(getattr(user, "is_verified_author", False)),
        "exp": int(exp_dt.timestamp()),
    }
    refresh_token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    sess = RefreshSession(
        user_id=user.id,
        refresh_token=refresh_token,
        user_agent=user_agent,
        ip=ip,
        created_at=_now(),
        expires_at=exp_dt,
        revoked=False,
    )
    db.add(sess)
    db.commit()
    return refresh_token

def rotate_refresh_session(db: Session, refresh_token: str, user_agent: str | None, ip: str | None) -> Tuple[str, str]:
    try:
        payload = decode_token(refresh_token)
    except JWTError as e:
        raise ValueError("Invalid refresh token") from e

    sess = (
        db.query(RefreshSession)
        .filter(RefreshSession.refresh_token == refresh_token, RefreshSession.revoked.is_(False))
        .one_or_none()
    )
    if sess is None:
        raise ValueError("Refresh session not found or revoked")
    if sess.expires_at <= _now():
        sess.revoked = True
        db.commit()
        raise ValueError("Refresh session expired")

    user = db.query(User).get(payload["uid"])
    if user is None:
        sess.revoked = True
        db.commit()
        raise ValueError("User not found")

    sess.revoked = True
    db.commit()

    new_access = create_access_token(user)
    new_refresh = create_refresh_session(db, user, user_agent=user_agent, ip=ip)
    return new_access, new_refresh

def revoke_refresh_session(db: Session, refresh_token: str) -> None:
    sess = (
        db.query(RefreshSession)
        .filter(RefreshSession.refresh_token == refresh_token, RefreshSession.revoked.is_(False))
        .one_or_none()
    )
    if sess:
        sess.revoked = True
        db.commit()
