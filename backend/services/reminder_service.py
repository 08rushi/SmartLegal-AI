"""
reminder_service.py — Reminders & Important Dates Management Engine (SL-059).

Allows Indian citizens to set, track, and receive alerts for legal deadlines
(e.g., Agreement Renewal Date, Lock-in Expiry, Rent Due Date, Passport Renewal).
"""

from datetime import datetime
import uuid
from typing import Dict, List, Any


# In-memory store fallback for development
_REMINDERS_STORE: Dict[str, List[Dict[str, Any]]] = {}


def create_reminder(
    user_id: str,
    title: str,
    due_date: str,
    category: str = "general",
    document_id: str = None,
    notes: str = None,
) -> Dict[str, Any]:
    """Create a new deadline reminder."""
    reminder = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": title,
        "due_date": due_date,
        "category": category,
        "document_id": document_id,
        "notes": notes,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }
    if user_id not in _REMINDERS_STORE:
        _REMINDERS_STORE[user_id] = []
    _REMINDERS_STORE[user_id].append(reminder)
    return reminder


def get_user_reminders(user_id: str) -> List[Dict[str, Any]]:
    """Get active reminders for a user."""
    return _REMINDERS_STORE.get(user_id, [])


def delete_reminder(user_id: str, reminder_id: str) -> bool:
    """Delete a reminder by ID."""
    if user_id in _REMINDERS_STORE:
        _REMINDERS_STORE[user_id] = [r for r in _REMINDERS_STORE[user_id] if r["id"] != reminder_id]
        return True
    return False
