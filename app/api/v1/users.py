from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import UserCreate, UserRead
from app.repos.user_repo import UserRepo
from app.core.deps import get_repos

router = APIRouter()

@router.post("/users", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, repos=Depends(get_repos)):
    users: UserRepo = repos["users"]
    if users.get_by_email(payload.email):
        raise HTTPException(409, "email already exists")
    return users.create(payload.model_dump())

@router.get("/users", response_model=list[UserRead])
def list_users(repos=Depends(get_repos)):
    users: UserRepo = repos["users"]
    return users.list()
