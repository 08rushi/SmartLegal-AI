"""
test_whatsapp.py — Step 1A WhatsApp Module & API Tests.

Verifies:
1. Module imports correctly.
2. Router registration in FastAPI app.
3. Development endpoint /api/v1/whatsapp/simulate-inbound is reachable and processes payloads.
4. Outbound summary endpoint /api/v1/whatsapp/send-summary functions correctly with auth headers.
"""

import pytest
from unittest.mock import AsyncMock
from schemas.whatsapp import (
    InboundMessagePayload,
    SimulatedMessageResponse,
    WhatsAppShareRequest,
)
from services.whatsapp import DevWhatsAppAdapter, WhatsAppOrchestrator
from routers.whatsapp import router as whatsapp_router


def test_whatsapp_module_imports():
    """Verify clean imports of all WhatsApp layer components."""
    adapter = DevWhatsAppAdapter()
    orchestrator = WhatsAppOrchestrator(adapter=adapter)
    
    assert adapter is not None
    assert orchestrator is not None
    assert whatsapp_router is not None


def test_simulate_inbound_endpoint_reachable(client):
    """Verify development simulated inbound endpoint handles POST requests."""
    payload = {
        "from_phone": "+919999000001",
        "message_text": "Hello SmartLegal AI",
        "message_id": "msg_sim_001",
    }
    
    response = client.post("/api/v1/whatsapp/simulate-inbound", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert data["received"]["from_phone"] == "+919999000001"
    assert data["received"]["message_text"] == "Hello SmartLegal AI"
    assert "SmartLegal AI" in data["reply"]
    assert "processed_at" in data


def test_simulate_inbound_validation_failures(client):
    """Verify request validation on missing required parameters."""
    # Missing message_text
    resp1 = client.post("/api/v1/whatsapp/simulate-inbound", json={"from_phone": "+919876543210"})
    assert resp1.status_code == 422

    # Empty message_text
    resp2 = client.post("/api/v1/whatsapp/simulate-inbound", json={"from_phone": "+919876543210", "message_text": "   "})
    assert resp2.status_code == 400


def test_send_summary_endpoint_authenticated(client, auth_headers_user_a):
    """Verify /send-summary endpoint queues summary delivery."""
    from routers.auth import get_current_user
    from main import app

    mock_user = {
        "id": "user_a_id_12345",
        "token_version": 0,
        "email": "user_a@example.com",
        "name": "User A",
    }
    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        payload = {
            "phone_number": "+919876543210",
            "document_name": "Rental Agreement.pdf",
            "risk_level": "Medium",
            "high_risk_count": 2,
            "obligations": ["Pay rent by 5th", "Maintain premises"],
        }
        
        resp = client.post("/api/v1/whatsapp/send-summary", json=payload, headers=auth_headers_user_a)
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["message"] == "WhatsApp summary queued successfully."
        assert data["details"]["recipient"] == "+919876543210"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
