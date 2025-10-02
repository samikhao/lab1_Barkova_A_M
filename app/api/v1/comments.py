from fastapi import APIRouter, Depends
from app.schemas.comment import CommentCreate, CommentUpdate, CommentRead
from app.core.deps import get_repos
from app.services.comment_service import CommentService

router = APIRouter()

def _service(repos):
    return CommentService(
        comments=repos["comments"], news=repos["news"], users=repos["users"]
    )

@router.post("/comments", response_model=CommentRead, status_code=201)
def create_comment(payload: CommentCreate, repos=Depends(get_repos)):
    svc = _service(repos)
    return svc.create(payload.model_dump())

@router.get("/comments", response_model=list[CommentRead])
def list_comments(repos=Depends(get_repos)):
    return repos["comments"].list()

@router.patch("/comments/{comment_id}", response_model=CommentRead)
def update_comment(comment_id: int, payload: CommentUpdate, repos=Depends(get_repos)):
    svc = _service(repos)
    return svc.update(comment_id, payload.model_dump(exclude_unset=True))
