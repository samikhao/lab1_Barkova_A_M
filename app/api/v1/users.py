from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserRead, UserVerify
from app.services.user_service import UserService
from app.core.deps import get_db, require_admin

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserRead, status_code=201)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    return await svc.create_user(payload.model_dump())

@router.get("/", response_model=list[UserRead])
async def list_users(db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    return await svc.list_users()

@router.post("/{user_id}/verify", response_model=UserRead, dependencies=[Depends(require_admin)])
async def verify_user(user_id: int, payload: UserVerify, db: AsyncSession = Depends(get_db)):
    svc = UserService(db)
    return await svc.set_verified(user_id, payload.is_verified_author)
