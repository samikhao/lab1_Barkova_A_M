from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_sso.sso.github import GithubSSO

from app.db.session import get_db
from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenPair,
    RefreshRequest,
    LogoutRequest,
    SessionPublic,
)
from app.services.auth_service import AuthService


router = APIRouter(tags=["auth"])

sso = GithubSSO(
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    redirect_uri=str(settings.GITHUB_REDIRECT_URL) if settings.GITHUB_REDIRECT_URL else None,
    allow_insecure_http=True,
)

def svc(db: AsyncSession) -> AuthService:
    return AuthService(db)

@router.post("/register", response_model=TokenPair, status_code=201)
async def register(req: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)) -> TokenPair:
    return await svc(db).register(req, request)

@router.post("/login", response_model=TokenPair)
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)) -> TokenPair:
    return await svc(db).login_password(req, request)

@router.post("/refresh", response_model=TokenPair)
async def refresh_tokens(req: RefreshRequest, request: Request, db: AsyncSession = Depends(get_db)) -> TokenPair:
    return await svc(db).refresh(req, request)

@router.post("/logout", status_code=204)
async def logout(req: LogoutRequest, db: AsyncSession = Depends(get_db)) -> None:
    return await svc(db).logout(req)

@router.get("/sessions", response_model=list[SessionPublic])
async def my_sessions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[SessionPublic]:
    return await svc(db).list_sessions(user)


@router.get("/github/login")
async def github_login(db: AsyncSession = Depends(get_db)):
    return await svc(db).github_login(sso)

@router.get("/github/callback", response_model=TokenPair)
async def github_callback(request: Request, db: AsyncSession = Depends(get_db)) -> TokenPair:
    return await svc(db).github_callback(request, sso)
