"""
test_legal_services.py — Indian Legal References & Statutory Retrieval Tests (SL-044).
"""

import pytest
from services.legal_reference_service import (
    verify_citation,
    enrich_clause_citations,
    CANONICAL_STATUTES,
)
from services.legal_retrieval_service import search_legal_corpus


def test_legal_reference_resolver():
    """Verify section citation resolution against canonical Indian statutes."""
    # BNS 2023 resolution
    ref = verify_citation("BNS", "318")
    assert ref is not None
    assert ref["verified"] is True
    assert "Bharatiya Nyaya Sanhita" in ref["statute"]

    # Contract Act resolution
    ref = verify_citation("CONTRACT", "73")
    assert ref is not None
    assert ref["verified"] is True
    assert "Contract" in ref["statute"]


def test_clause_citation_enrichment():
    """Verify automatic clause citation extraction and enrichment."""
    clauses = [{
        "clause_text": "Tenant shall pay rent by the 5th of every month.",
        "risk_reason": "Breach of contract under section 73 of contract act.",
    }]
    enriched = enrich_clause_citations(clauses)
    assert len(enriched) == 1
    assert "verified_legal_refs" in enriched[0]
    assert len(enriched[0]["verified_legal_refs"]) >= 1


@pytest.mark.anyio
async def test_legal_retrieval_service():
    """Verify statutory corpus search function."""
    results = await search_legal_corpus("rent", domain="property", limit=5)
    assert isinstance(results, list)


