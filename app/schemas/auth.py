from datetime import datetime
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access: str
    refresh: str


class RefreshRequest(BaseModel):
    refresh: str


class LogoutRequest(BaseModel):
    refresh: str


class SessionPublic(BaseModel):
    id: int
    user_agent: str | None
    ip: str | None
    created_at: datetime
    expires_at: datetime
    revoked: bool
