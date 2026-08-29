"""
admin_kb_service.py — Admin Knowledge Management Engine (SL-077).

Manages dynamic updates to civic service fees, timelines, statutory guidance, and FAQs.
"""

from datetime import datetime
import uuid
from typing import Dict, List, Any

_DYNAMIC_KB: Dict[str, Dict[str, Any]] = {}


def upsert_kb_article(
    title: str,
    category: str,
    content: str,
    statutes: List[str] = None,
    fees_inr: int = 0,
    official_url: str = None,
) -> Dict[str, Any]:
    """Upsert dynamic legal/service article."""
    article_id = str(uuid.uuid4())
    article = {
        "id": article_id,
        "title": title,
        "category": category,
        "content": content,
        "statutes": statutes or [],
        "fees_inr": fees_inr,
        "official_url": official_url,
        "updated_at": datetime.utcnow().isoformat(),
    }
    _DYNAMIC_KB[article_id] = article
    return article


def get_all_kb_articles() -> List[Dict[str, Any]]:
    """Get all dynamic KB articles."""
    return list(_DYNAMIC_KB.values())
