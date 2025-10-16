from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from jose import JWTError
from fastapi_sso.sso.github import GithubSSO

from app.db.session import get_db
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_session,
    rotate_refresh_session,
    revoke_refresh_session,
)
from app.core.deps import get_current_user
from app.models.user import User
from app.models.refresh_session import RefreshSession
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenPair,
    RefreshRequest,
    LogoutRequest,
    SessionPublic,
)

router = APIRouter(tags=["auth"])

@router.post("/register", response_model=TokenPair, status_code=201)
def register(req: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    exists = db.query(User).filter(User.email == req.email).one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(name=req.name, email=req.email, password_hash=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    access = create_access_token(user)
    refresh = create_refresh_session(
        db,
        user,
        user_agent=request.headers.get("User-Agent"),
        ip=(request.client.host if request.client else None),
    )
    return TokenPair(access=access, refresh=refresh)

@router.post("/login", response_model=TokenPair)
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    user = db.query(User).filter(User.email == req.email).one_or_none()
    if not user or not user.password_hash or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_access_token(user)
    refresh = create_refresh_session(
        db,
        user,
        user_agent=request.headers.get("User-Agent"),
        ip=(request.client.host if request.client else None),
    )
    return TokenPair(access=access, refresh=refresh)


@router.post("/refresh", response_model=TokenPair)
def refresh_tokens(req: RefreshRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    try:
        access, refresh = rotate_refresh_session(
            db,
            req.refresh,
            user_agent=request.headers.get("User-Agent"),
            ip=(request.client.host if request.client else None),
        )
    except (ValueError, JWTError) as e:
        raise HTTPException(status_code=401, detail=str(e))
    return TokenPair(access=access, refresh=refresh)

@router.post("/logout", status_code=204)
def logout(req: LogoutRequest, db: Session = Depends(get_db)) -> None:
    revoke_refresh_session(db, req.refresh)

@router.get("/sessions", response_model=list[SessionPublic])
def my_sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[SessionPublic]:
    rows = (
        db.query(RefreshSession)
        .filter(RefreshSession.user_id == user.id)
        .order_by(RefreshSession.created_at.desc())
        .all()
    )
    return [
        SessionPublic(
            id=r.id,
            user_agent=r.user_agent,
            ip=r.ip,
            created_at=r.created_at,
            expires_at=r.expires_at,
            revoked=r.revoked,
        )
        for r in rows
    ]


sso = GithubSSO(
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    redirect_uri=str(settings.GITHUB_REDIRECT_URL) if settings.GITHUB_REDIRECT_URL else None,
    allow_insecure_http=True,
)

@router.get("/github/login")
async def github_login():
    return await sso.get_login_redirect()

@router.get("/github/callback", response_model=TokenPair)
async def github_callback(request: Request, db: Session = Depends(get_db)) -> TokenPair:
    async with sso:
        gh_user = await sso.verify_and_process(request)

    if not gh_user:
        raise HTTPException(status_code=401, detail="GitHub auth failed")

    user = db.query(User).filter(User.github_id == str(gh_user.id)).one_or_none()
    if not user:
        if gh_user.email:
            user = db.query(User).filter(User.email == gh_user.email).one_or_none()
        if user:
            user.github_id = str(gh_user.id)
            if gh_user.picture and not user.avatar_url:
                user.avatar_url = gh_user.picture
        else:
            user = User(
                name=gh_user.display_name or "GitHub User",
                email=gh_user.email or f"gh_{gh_user.id}@example.com",
                github_id=str(gh_user.id),
                avatar_url=gh_user.picture,
            )
            db.add(user)
        db.commit()
        db.refresh(user)

    access = create_access_token(user)
    refresh = create_refresh_session(
        db,
        user,
        user_agent=request.headers.get("User-Agent"),
        ip=(request.client.host if request.client else None),
    )
    return TokenPair(access=access, refresh=refresh)
