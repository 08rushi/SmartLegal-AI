"""
billing_service.py — Subscriptions, Quotas & Usage Billing Engine (SL-074).

Manages user tier quotas (Free, Pro, Enterprise), checks AI usage limits, and tracks ledger.
"""

from typing import Dict, Any

PLANS: Dict[str, Dict[str, Any]] = {
    "free": {
        "name": "Citizen Free Tier",
        "monthly_documents": 3,
        "price_inr": 0,
        "features": ["Basic PDF Analysis", "Hindi Translation", "Single Document Q&A"],
    },
    "pro": {
        "name": "Citizen Pro",
        "monthly_documents": 100,
        "price_inr": 499,
        "features": ["Priority AI Analysis", "Cross-Document AI", "WhatsApp Alerts", "Clause Rewriter"],
    },
    "enterprise": {
        "name": "Legal Firm Enterprise",
        "monthly_documents": 99999,
        "price_inr": 4999,
        "features": ["Unlimited Analysis", "Organization Workspaces", "Advocate Review Network"],
    },
}

# In-memory quota tracker fallback
_USAGE_LEDGER: Dict[str, int] = {}
_USER_PLANS: Dict[str, str] = {}


def get_user_plan(user_id: str) -> str:
    """Get active plan for a user (default 'free')."""
    return _USER_PLANS.get(user_id, "free")


def check_user_quota(user_id: str) -> Dict[str, Any]:
    """Check if user has remaining document analysis quota."""
    plan_code = get_user_plan(user_id)
    plan = PLANS.get(plan_code, PLANS["free"])

    used_count = _USAGE_LEDGER.get(user_id, 0)
    monthly_limit = plan["monthly_documents"]
    allowed = used_count < monthly_limit

    return {
        "allowed": allowed,
        "plan": plan_code,
        "used": used_count,
        "limit": monthly_limit,
        "remaining": max(0, monthly_limit - used_count),
    }


def record_usage_increment(user_id: str) -> int:
    """Increment monthly document analysis count."""
    current = _USAGE_LEDGER.get(user_id, 0)
    _USAGE_LEDGER[user_id] = current + 1
    return _USAGE_LEDGER[user_id]
