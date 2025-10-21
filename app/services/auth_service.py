from __future__ import annotations

from datetime import datetime, timezone
from fastapi import HTTPException, Request
from jose import JWTError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

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

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepo(db)

    async def _rs_create(self, *, user_id: int, token: str, ua: str | None, ip: str | None, expires_at):
        obj = RefreshSession(
            user_id=user_id, refresh_token=token, user_agent=ua, ip=ip, expires_at=expires_at
        )
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def _rs_find_active(self, token: str) -> RefreshSession | None:
        return await self.db.scalar(
            select(RefreshSession).where(
                RefreshSession.refresh_token == token,
                RefreshSession.revoked.is_(False),
            )
        )

    async def _rs_revoke(self, token: str) -> None:
        await self.db.execute(
            update(RefreshSession)
            .where(RefreshSession.refresh_token == token, RefreshSession.revoked.is_(False))
            .values(revoked=True)
        )
        await self.db.commit()

    async def _rs_list_for_user(self, user_id: int) -> list[RefreshSession]:
        res = await self.db.scalars(
            select(RefreshSession)
            .where(RefreshSession.user_id == user_id)
            .order_by(RefreshSession.created_at.desc())
        )
        return res.all()

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
        if not sess:
            raise HTTPException(status_code=401, detail="Refresh session not found or revoked")
        if sess.expires_at <= datetime.now(timezone.utc):
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
        rows = await self._rs_list_for_user(user.id)
        return [
            SessionPublic(
                id=r.id,
                user_agent=r.user_agent,
                ip=r.ip,
                created_at=r.created_at,
                expires_at=r.expires_at,
                revoked=r.revoked,
            ) for r in rows
        ]

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
