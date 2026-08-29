"""
org_service.py — Organization Workspaces & Team Permissions Engine (SL-075).

Allows legal firms, businesses, and family accounts to collaborate on legal documents with RBAC.
"""

from datetime import datetime
import uuid
from typing import Dict, List, Any

_ORGS: Dict[str, Dict[str, Any]] = {}
_MEMBERS: Dict[str, List[Dict[str, Any]]] = {}

ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "owner": ["manage_members", "upload", "analyze", "delete", "share"],
    "admin": ["manage_members", "upload", "analyze", "share"],
    "reviewer": ["upload", "analyze"],
    "viewer": ["read_only"],
}


def create_organization(owner_user_id: str, org_name: str) -> Dict[str, Any]:
    """Create a new team organization workspace."""
    org_id = str(uuid.uuid4())
    org = {
        "id": org_id,
        "name": org_name,
        "owner_id": owner_user_id,
        "created_at": datetime.utcnow().isoformat(),
    }
    _ORGS[org_id] = org

    # Add owner as first member
    _MEMBERS[org_id] = [
        {
            "user_id": owner_user_id,
            "role": "owner",
            "joined_at": datetime.utcnow().isoformat(),
        }
    ]
    return org


def add_org_member(org_id: str, email: str, role: str = "reviewer") -> Dict[str, Any]:
    """Invite/add member to an organization."""
    if org_id not in _ORGS:
        raise ValueError("Organization not found.")

    member = {
        "user_id": f"usr_{uuid.uuid4().hex[:8]}",
        "email": email.lower(),
        "role": role if role in ROLE_PERMISSIONS else "viewer",
        "joined_at": datetime.utcnow().isoformat(),
    }
    _MEMBERS[org_id].append(member)
    return member


def get_org_members(org_id: str) -> List[Dict[str, Any]]:
    """Retrieve members of an organization."""
    return _MEMBERS.get(org_id, [])
