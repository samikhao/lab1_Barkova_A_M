from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserRead, UserVerify
from app.repos.user_repo import UserRepo
from app.core.deps import get_repos, get_db

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserRead, status_code=201)
async def create_user(payload: UserCreate, repos=Depends(get_repos)):
    users: UserRepo = repos["users"]
    if await users.get_by_email(payload.email):
        raise HTTPException(409, "email already exists")
    return await users.create(payload.model_dump())

@router.get("/", response_model=list[UserRead])
async def list_users(repos=Depends(get_repos)):
    users: UserRepo = repos["users"]
    return await users.list()

@router.post("/{user_id}/verify", response_model=UserRead)
async def verify_user(user_id: int, payload: UserVerify, db: AsyncSession = Depends(get_db)):
    repo = UserRepo(db)
    user = await repo.set_verified(user_id, payload.is_verified_author)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
