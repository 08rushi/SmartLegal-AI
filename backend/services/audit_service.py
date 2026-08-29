"""
audit_service.py — Immutable Audit & Security Event Logging Engine (SL-078).

Records security-sensitive actions (login, document access, share link creation, deletion)
for compliance and incident audit trails.
"""

from datetime import datetime
import uuid
from typing import Dict, List, Any

_AUDIT_LOGS: List[Dict[str, Any]] = []


def record_audit_event(
    user_id: str,
    event_type: str,
    resource_id: str = None,
    ip_address: str = "127.0.0.1",
    details: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Record an append-only security audit log entry."""
    entry = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "event_type": event_type,
        "resource_id": resource_id,
        "ip_address": ip_address,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat(),
    }
    _AUDIT_LOGS.append(entry)
    print(f"[Audit Log] {entry['timestamp']} | User: {user_id} | Event: {event_type} | Resource: {resource_id}")
    return entry


def get_user_audit_logs(user_id: str) -> List[Dict[str, Any]]:
    """Get audit logs for a specific user."""
    return [log for log in _AUDIT_LOGS if log["user_id"] == user_id]
