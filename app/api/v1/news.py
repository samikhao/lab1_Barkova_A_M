from fastapi import APIRouter, Depends
from app.schemas.news import NewsCreate, NewsUpdate, NewsRead
from app.core.deps import get_repos
from app.services.news_service import NewsService
from app.repos.news_repo import NewsRepo

router = APIRouter(prefix="/news", tags=["news"])

def _service(repos):
    return NewsService(users=repos["users"], news=repos["news"])

@router.post("/", response_model=NewsRead, status_code=201)
def create_news(payload: NewsCreate, repos=Depends(get_repos)):
    svc = _service(repos)
    return svc.create(payload.model_dump())

@router.get("/", response_model=list[NewsRead])
def list_news(repos=Depends(get_repos)):
    news: NewsRepo = repos["news"]
    return news.list()

@router.patch("/{news_id}", response_model=NewsRead)
def update_news(news_id: int, payload: NewsUpdate, repos=Depends(get_repos)):
    svc = _service(repos)
    return svc.update(news_id, payload.model_dump(exclude_unset=True))

@router.delete("/{news_id}", status_code=204)
def delete_news(news_id: int, repos=Depends(get_repos)):
    svc = _service(repos)
    svc.delete(news_id)
    return
