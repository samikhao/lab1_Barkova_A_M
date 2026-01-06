from fastapi import APIRouter, Depends
from app.schemas.comment import CommentCreate, CommentUpdate, CommentRead
from app.core.deps import get_repos, get_current_user, require_comment_owner_or_admin
from app.services.comment_service import CommentService
from app.models.user import User

router = APIRouter(prefix="/comments", tags=["comments"])

def _service(repos):
    return CommentService(
        comments=repos["comments"], news=repos["news"], users=repos["users"]
    )

@router.post("/", response_model=CommentRead, status_code=201)
async def create_comment(payload: CommentCreate, repos=Depends(get_repos), user: User = Depends(get_current_user)):
    svc = _service(repos)
    return await svc.create(payload.model_dump() | {"author_id": user.id})

@router.get("/", response_model=list[CommentRead])
async def list_comments(repos=Depends(get_repos)):
    return await repos["comments"].list()

@router.patch("/{comment_id}", response_model=CommentRead, dependencies=[Depends(require_comment_owner_or_admin)])
async def update_comment(comment_id: int, payload: CommentUpdate, repos=Depends(get_repos)):
    svc = _service(repos)
    return await svc.update(comment_id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/{comment_id}",
    status_code=204,
    dependencies=[Depends(require_comment_owner_or_admin)],
)
async def delete_comment(comment_id: int, repos=Depends(get_repos)):
    svc = _service(repos)
    await svc.delete(comment_id)
    return
