"""
share_service.py — Granular Time-Bound Document Sharing Engine (SL-076).

Generates secure, expiring share tokens for read-only document access.
"""

from datetime import datetime, timedelta
import secrets
from typing import Dict, Any, Optional

_SHARE_GRANTS: Dict[str, Dict[str, Any]] = {}


def create_share_grant(
    owner_user_id: str,
    document_id: str,
    expiration_hours: int = 72,
    permission: str = "read_only",
) -> Dict[str, Any]:
    """Create a time-bound share grant."""
    token = secrets.token_urlsafe(24)
    expires_at = (datetime.utcnow() + timedelta(hours=expiration_hours)).isoformat()

    grant = {
        "token": token,
        "document_id": document_id,
        "owner_user_id": owner_user_id,
        "permission": permission,
        "expires_at": expires_at,
        "revoked": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    _SHARE_GRANTS[token] = grant
    return grant


def get_share_grant(token: str) -> Optional[Dict[str, Any]]:
    """Retrieve and validate a share grant."""
    grant = _SHARE_GRANTS.get(token)
    if not grant or grant["revoked"]:
        return None

    expires = datetime.fromisoformat(grant["expires_at"])
    if datetime.utcnow() > expires:
        return None

    return grant


def revoke_share_grant(owner_user_id: str, token: str) -> bool:
    """Revoke an active share grant."""
    grant = _SHARE_GRANTS.get(token)
    if grant and grant["owner_user_id"] == owner_user_id:
        grant["revoked"] = True
        return True
    return False
