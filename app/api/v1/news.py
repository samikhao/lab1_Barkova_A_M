from fastapi import APIRouter, Depends
from app.schemas.news import NewsCreate, NewsUpdate, NewsRead
from app.core.deps import get_repos, get_current_user, require_author_verified, require_news_owner_or_admin
from app.services.news_service import NewsService
from app.repos.news_repo import NewsRepo
from app.models.user import User

router = APIRouter(prefix="/news", tags=["news"])

def _service(repos):
    return NewsService(users=repos["users"], news=repos["news"])

@router.post("/", response_model=NewsRead, status_code=201, dependencies=[Depends(require_author_verified)])
def create_news(payload: NewsCreate, repos=Depends(get_repos), user: User = Depends(get_current_user)):
    svc = _service(repos)
    return svc.create(payload.model_dump() | {"author_id": user.id})

@router.get("/", response_model=list[NewsRead])
def list_news(repos=Depends(get_repos)):
    news: NewsRepo = repos["news"]
    return news.list()

@router.patch("/{news_id}", response_model=NewsRead, dependencies=[Depends(require_news_owner_or_admin)])
def update_news(news_id: int, payload: NewsUpdate, repos=Depends(get_repos)):
    svc = _service(repos)
    return svc.update(news_id, payload.model_dump(exclude_unset=True))

@router.delete("/{news_id}", status_code=204, dependencies=[Depends(require_news_owner_or_admin)])
def delete_news(news_id: int, repos=Depends(get_repos)):
    svc = _service(repos)
    svc.delete(news_id)
    return
