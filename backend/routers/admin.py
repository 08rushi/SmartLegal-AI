from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.admin_kb_service import upsert_kb_article, get_all_kb_articles
from routers.auth import get_current_user

router = APIRouter()


class ArticleUpsertRequest(BaseModel):
    title: str
    category: str
    content: str
    statutes: list[str] = []
    fees_inr: int = 0
    official_url: str = None


@router.post("/articles")
async def create_or_update_article(
    req: ArticleUpsertRequest,
    current_user=Depends(get_current_user),
):
    """Upsert dynamic knowledge base article (SL-077)."""
    article = upsert_kb_article(
        req.title, req.category, req.content, req.statutes, req.fees_inr, req.official_url
    )
    return {"message": "Article updated successfully.", "article": article}


@router.get("/articles")
async def list_admin_articles(current_user=Depends(get_current_user)):
    """List all dynamic knowledge articles (SL-077)."""
    return {"articles": get_all_kb_articles()}
