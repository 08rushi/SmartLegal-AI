"""
whatsapp.py — WhatsApp Bot API Router.

Endpoints for simulated inbound WhatsApp message handling, Meta Cloud API webhook
verification & event reception, and outbound document summary sharing.
"""

import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status, BackgroundTasks

from database import get_db, get_db_ctx
from config import get_settings
from schemas.whatsapp import (
    InboundMessagePayload,
    SimulatedMessageResponse,
    WhatsAppShareRequest,
    WhatsAppShareResponse,
)
from services.whatsapp import WhatsAppOrchestrator, MetaWhatsAppAdapter
from services.whatsapp.repository import get_or_create_whatsapp_contact
from services.whatsapp.reliability import claim_message_processing
from services.whatsapp_service import format_whatsapp_analysis_summary, send_whatsapp_message
from routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()
dev_orchestrator = WhatsAppOrchestrator()
meta_adapter = MetaWhatsAppAdapter()
meta_orchestrator = WhatsAppOrchestrator(adapter=meta_adapter)

MAX_WEBHOOK_PAYLOAD_SIZE = 1 * 1024 * 1024  # 1 MB maximum payload ceiling


async def verify_meta_signature_and_get_raw_body(request: Request) -> bytes:
    """
    Dependency verifying Meta Cloud API POST webhook HMAC-SHA256 signature (X-Hub-Signature-256).
    Enforces a strict 1 MB payload size ceiling during streaming consumption for both known
    and unknown/chunked Content-Length headers, and performs constant-time signature comparison.
    Raises:
    - HTTP 413: Request body exceeds 1 MB limit (pre-check or during stream reading).
    - HTTP 401: Missing, malformed, or invalid X-Hub-Signature-256 header.
    """
    # 1. Pre-check Content-Length header if present
    content_length_hdr = request.headers.get("Content-Length") or request.headers.get("content-length")
    if content_length_hdr and content_length_hdr.isdigit():
        if int(content_length_hdr) > MAX_WEBHOOK_PAYLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Webhook payload size exceeds maximum limit of 1 MB.",
            )

    # 2. Hard Streaming Size Protection (Enforced chunk-by-chunk for known & unknown/chunked Content-Length)
    body_buffer = bytearray()
    total_bytes = 0

    try:
        async for chunk in request.stream():
            total_bytes += len(chunk)
            if total_bytes > MAX_WEBHOOK_PAYLOAD_SIZE:
                logger.warning(f"[whatsapp-router] Inbound webhook body exceeded 1 MB ceiling during stream read ({total_bytes} bytes).")
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Webhook payload size exceeds maximum limit of 1 MB.",
                )
            body_buffer.extend(chunk)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read request body stream.",
        )

    raw_body = bytes(body_buffer)

    # 3. HMAC-SHA256 Signature Verification
    app_secret = settings.meta_whatsapp_app_secret
    if not app_secret or not app_secret.strip():
        if settings.is_production:
            # Production: fail closed — do not accept webhooks without a configured app secret.
            # This prevents forged payloads from being processed when the secret is accidentally omitted.
            logger.error(
                "[whatsapp-router] META_WHATSAPP_APP_SECRET is not configured in production. "
                "Rejecting inbound webhook to prevent unauthenticated payload processing."
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Webhook endpoint is not available: signature verification is not configured.",
            )
        # Non-production: deliberate dev-mode bypass — emit an explicit warning and skip HMAC.
        # This path must NEVER be reachable in a production deployment.
        logger.warning(
            "[whatsapp-router] META_WHATSAPP_APP_SECRET is not configured. "
            "HMAC signature verification is DISABLED. This is only safe in non-production environments."
        )
        return raw_body

    signature_header = request.headers.get("X-Hub-Signature-256") or request.headers.get("x-hub-signature-256")
    if not signature_header or not signature_header.strip():
        logger.warning("[whatsapp-router] Missing X-Hub-Signature-256 header on inbound webhook POST.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Hub-Signature-256 header.",
        )

    clean_sig_header = signature_header.strip()
    if not clean_sig_header.startswith("sha256="):
        logger.warning("[whatsapp-router] Malformed X-Hub-Signature-256 header format.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature format. Must begin with 'sha256='.",
        )

    provided_sig = clean_sig_header[7:].strip()
    secret_bytes = app_secret.strip().encode("utf-8")
    expected_hex = hmac.new(secret_bytes, raw_body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(provided_sig, expected_hex):
        logger.warning("[whatsapp-router] HMAC signature mismatch for inbound Meta webhook.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook signature verification failed.",
        )

    return raw_body


async def _process_inbound_background(msg_payload_dict: Dict[str, Any], db: Optional[Any] = None):
    """
    Async background task executing heavy orchestrator processing after HTTP 200 ack.
    Acquires its own independent database connection lifecycle to avoid using closed request-scoped connections.
    """
    try:
        if db is not None:
            # Test fixture path: reuse provided test DB connection wrapper
            await meta_orchestrator.process_inbound_message(msg_payload_dict, db=db)
        else:
            # Production path: Acquire fresh, independent DB connection context from pool
            async with get_db_ctx() as bg_db:
                await meta_orchestrator.process_inbound_message(msg_payload_dict, db=bg_db)
    except Exception as exc:
        logger.error(f"[whatsapp-webhook-bg] Background processing failed: {exc}")


@router.get(
    "/webhook",
    summary="Meta WhatsApp Cloud API Webhook Verification (GET)",
    description="Endpoint for Meta to verify webhook endpoint ownership using hub.verify_token and hub.challenge.",
)
async def verify_meta_whatsapp_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """
    Meta Cloud API Webhook Verification endpoint.
    Performs secure constant-time token comparison against settings.meta_whatsapp_verify_token.
    """
    if hub_mode != "subscribe" or not hub_verify_token or not hub_challenge:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook verification request parameters.",
        )

    configured_token = settings.meta_whatsapp_verify_token
    if not configured_token or not configured_token.strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Meta WhatsApp verify token is not configured on server.",
        )

    if not hmac.compare_digest(hub_verify_token.strip(), configured_token.strip()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verification token mismatch.",
        )

    return Response(content=hub_challenge, media_type="text/plain", status_code=200)


@router.post(
    "/webhook",
    summary="Meta WhatsApp Cloud API Webhook Event Receiver (POST)",
    description="Endpoint to receive Meta Cloud API webhook events, verify HMAC-SHA256 signature, deduplicate via Step 2G, and schedule async background processing.",
)
async def receive_meta_whatsapp_webhook(
    background_tasks: BackgroundTasks,
    raw_body: bytes = Depends(verify_meta_signature_and_get_raw_body),
    db=Depends(get_db),
):
    """
    Production Meta Cloud API POST Webhook event receiver.
    Verifies HMAC signature, validates JSON payload, extracts mandatory wamids,
    claims Step 2G ownership, schedules async background task with independent DB lifecycle, and returns HTTP 200 immediately.
    """
    # 1. Parse JSON Payload from Raw Bytes
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON payload.",
        )

    # 2. Extract & Validate Inbound Message Payloads
    try:
        inbound_messages = meta_adapter.extract_inbound_payloads(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook payload: {str(exc)}",
        )

    if not inbound_messages:
        # Non-message event or status notification
        return {"status": "ignored", "detail": "Non-message or status notification event"}

    scheduled_count = 0

    # 3. Process Each Inbound Message Payload (Step 2G Claim & Background Schedule)
    for msg_payload in inbound_messages:
        msg_dict = msg_payload.model_dump()
        wamid = msg_payload.message_id

        if not wamid or not wamid.strip():
            logger.warning("[whatsapp-router] Inbound user message missing mandatory wamid. Ignoring.")
            continue

        contact_id = "wac_dev"
        if db is not None:
            contact = await get_or_create_whatsapp_contact(db, phone_number=msg_payload.from_phone)
            contact_id = contact["id"]

            claim_res = await claim_message_processing(db, wamid, contact_id)
            if not claim_res.get("is_owner"):
                logger.info(f"[whatsapp-router] Event {wamid} already claimed or completed. Skipping background task.")
                continue

        # Schedule Heavy Orchestration & Outbound Dispatcher as Async Background Task
        # Background task receives msg_dict and acquires its own independent DB connection context
        background_tasks.add_task(_process_inbound_background, msg_dict)
        scheduled_count += 1

    return {"status": "ok", "processed_count": scheduled_count}


@router.post(
    "/simulate-inbound",
    response_model=SimulatedMessageResponse,
    summary="Simulate incoming WhatsApp message (Dev endpoint)",
    description="Development-safe endpoint to simulate incoming messages from WhatsApp users.",
)
async def simulate_inbound_whatsapp_message(
    payload: InboundMessagePayload,
    db=Depends(get_db),
):
    """
    Development API endpoint to receive and process simulated incoming WhatsApp messages.
    """
    if not payload.from_phone or not payload.from_phone.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field 'from_phone' is required.",
        )
    if not payload.message_text or not payload.message_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field 'message_text' is required.",
        )

    response = await dev_orchestrator.process_inbound_message(payload.model_dump(), db=db)
    return response


@router.post(
    "/send-summary",
    response_model=WhatsAppShareResponse,
    summary="Send document summary to WhatsApp (SL-072)",
)
async def send_summary_to_whatsapp(
    req: WhatsAppShareRequest,
    current_user=Depends(get_current_user),
):
    """Send document analysis summary to WhatsApp."""
    if not req.phone_number:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mobile phone number required.")

    formatted_msg = format_whatsapp_analysis_summary(
        req.document_name, req.risk_level, req.high_risk_count, req.obligations
    )
    result = send_whatsapp_message(req.phone_number, formatted_msg)
    return WhatsAppShareResponse(
        message="WhatsApp summary queued successfully.",
        details=result,
    )
