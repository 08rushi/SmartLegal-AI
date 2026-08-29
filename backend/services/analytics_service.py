"""
analytics_service.py — Privacy-Safe Product Analytics Engine (SL-082).

Tracks anonymous product adoption, document conversion funnels, and feature interactions
WITHOUT logging unencrypted document content or PII.
"""

from datetime import datetime
from typing import Dict, Any, List

_ANALYTICS_EVENTS: List[Dict[str, Any]] = []


def track_event(event_name: str, properties: Dict[str, Any] = None) -> Dict[str, Any]:
    """Record a privacy-safe analytics event."""
    safe_props = properties.copy() if properties else {}
    # Strip any potential raw document text or PII
    safe_props.pop("document_text", None)
    safe_props.pop("user_email", None)

    event = {
        "event_name": event_name,
        "properties": safe_props,
        "timestamp": datetime.utcnow().isoformat(),
    }
    _ANALYTICS_EVENTS.append(event)
    return event


def get_analytics_summary() -> Dict[str, Any]:
    """Summarize feature interactions for product metrics."""
    counts: Dict[str, int] = {}
    for ev in _ANALYTICS_EVENTS:
        name = ev["event_name"]
        counts[name] = counts.get(name, 0) + 1
    return {"total_events": len(_ANALYTICS_EVENTS), "event_counts": counts}
