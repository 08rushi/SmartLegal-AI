"""
legal_retrieval_service.py — Reusable Legal Retrieval Engine (SL-030).

Provides a domain-filterable retrieval interface for legal acts, clauses, and guidance.
Architected to support lexical keyword matching now, with seamless drop-in
upgrade path for PostgreSQL full-text search and pgvector semantic search.
"""

from typing import List, Dict, Any, Optional
from services.indian_law_kb import get_statute_by_keyword, get_relevant_acts
from services.legal_id_kb import get_id_guidance
from services.property_kb import get_property_guidance
from services.business_kb import get_business_guidance


async def search_legal_corpus(
    query: str,
    domain: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Search legal corpus for statutory provisions, guidance, and legal rules.
    Returns ranked result objects with metadata, relevance score, and source act.
    """
    q = query.strip().lower()
    results = []

    # 1. Statutory search against Indian Law Knowledge Base
    acts = get_relevant_acts(q)
    for act in acts[:limit]:
        title = act if isinstance(act, str) else act.get("name", "Indian Statute")
        results.append({
            "source_type": "statute",
            "title": title,
            "section": act.get("section", "") if isinstance(act, dict) else "",
            "summary": act.get("summary", "") if isinstance(act, dict) else "",
            "key_takeaway": act.get("key_takeaway", "") if isinstance(act, dict) else "",
            "relevance_score": 0.95,
        })


    # 2. Domain-specific guidance retrieval
    if domain == "legal-id" or not domain:
        for id_key in ["aadhaar", "pan", "passport", "voter_id", "driving_licence"]:
            guidance = get_id_guidance(id_key)
            if guidance and any(kw in q for kw in [id_key, guidance.get("display_name", "").lower()]):
                results.append({
                    "source_type": "civic_guidance",
                    "domain": "legal-id",
                    "title": guidance.get("display_name"),
                    "summary": f"Official guidance for {guidance.get('display_name')} issued by {guidance.get('authority')}.",
                    "relevance_score": 0.90,
                })

    if domain == "property" or not domain:
        for prop_key in ["rental_agreement", "sale_deed", "land_mutation", "encumbrance_certificate"]:
            guidance = get_property_guidance(prop_key)
            if guidance and any(kw in q for kw in [prop_key.replace("_", " "), guidance.get("display_name", "").lower()]):
                results.append({
                    "source_type": "civic_guidance",
                    "domain": "property",
                    "title": guidance.get("display_name"),
                    "summary": f"Official property guidance for {guidance.get('display_name')}.",
                    "relevance_score": 0.90,
                })

    # Rank results by relevance_score
    results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    return results[:limit]
