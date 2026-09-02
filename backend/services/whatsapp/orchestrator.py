"""
orchestrator.py — WhatsApp Bot Conversation Orchestrator.

Sits between the WhatsApp Adapter and core SmartLegal AI services.
Coordinates multi-turn dialogue, onboarding state, mandatory language selection,
and localized response routing.
"""

import datetime
from typing import Optional, Dict, Any
from schemas.whatsapp import InboundMessagePayload, SimulatedMessageResponse
from services.whatsapp.adapter import BaseWhatsAppAdapter, DevWhatsAppAdapter
from services.whatsapp.repository import (
    get_or_create_whatsapp_contact,
    save_whatsapp_message,
    update_contact_language,
    reset_contact_onboarding,
    get_whatsapp_message_history,
)
from services.whatsapp.language import (
    WhatsAppSessionContext,
    parse_language_selection,
    is_language_change_command,
    is_menu_command,
    WELCOME_LANGUAGE_SELECTION_PROMPT,
    INVALID_LANGUAGE_SELECTION_PROMPT,
    get_localized_continuation_message,
)
from services.whatsapp.intent import detect_intent, IntentType
from services.whatsapp.boundaries import WhatsAppCapabilityRouter
from services.whatsapp.reliability import (
    normalize_event_identity,
    claim_message_processing,
    complete_message_processing,
    fail_message_processing,
)
from services.whatsapp.outbound_dispatcher import send_outbound_message


class WhatsAppOrchestrator:
    """
    Decoupled conversation orchestrator for WhatsApp interactions.
    """

    def __init__(self, adapter: Optional[BaseWhatsAppAdapter] = None):
        self.adapter = adapter or DevWhatsAppAdapter()

    async def process_inbound_message(
        self,
        raw_payload: Dict[str, Any],
        db: Any = None,
    ) -> SimulatedMessageResponse:
        """
        Process incoming WhatsApp message through onboarding, language resolution, and conversation orchestration.
        Guarantees effectively-once logical business outcomes for duplicate inbound webhook events.
        """
        inbound: InboundMessagePayload = self.adapter.parse_inbound_payload(raw_payload)
        text = inbound.message_text.strip() if inbound.message_text else ""

        # Step 1: Session Context & Idempotency Key Normalization
        if db is not None:
            contact = await get_or_create_whatsapp_contact(db, phone_number=inbound.from_phone)
            contact_id = contact["id"]
            ctx = WhatsAppSessionContext(
                contact_id=contact["id"],
                phone_number=contact["phone_number"],
                user_id=contact.get("user_id"),
                preferred_language=contact.get("preferred_language"),
                onboarding_status=contact.get("onboarding_status", "pending"),
            )
        else:
            contact_id = "wac_dev"
            ctx = WhatsAppSessionContext(
                contact_id="wac_dev",
                phone_number=inbound.from_phone,
                preferred_language=None,
                onboarding_status="pending",
            )

        provider_msg_id = normalize_event_identity(inbound, contact_id)

        # Step 2: Idempotency Claim & Replay Prevention
        if db is not None and ctx.contact_id != "wac_dev":
            claim_res = await claim_message_processing(db, provider_msg_id, contact_id)
            if not claim_res["is_owner"]:
                processed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                return SimulatedMessageResponse(
                    status="ok",
                    received=inbound,
                    reply=claim_res.get("outbound_reply") or "Duplicate event in progress or completed.",
                    processed_at=processed_at,
                )

        try:
            # Step 3: Inbound Database Persistence
            if db is not None and ctx.contact_id != "wac_dev":
                await save_whatsapp_message(
                    db,
                    contact_id=ctx.contact_id,
                    direction="inbound",
                    content=inbound.message_text,
                    message_type=inbound.message_type or "text",
                    media_url=inbound.media_url,
                    provider_message_id=provider_msg_id,
                )

            # Step 4: Check for Language Reset Command
            if is_language_change_command(text):
                if db is not None and ctx.contact_id != "wac_dev":
                    await reset_contact_onboarding(db, ctx.contact_id)
                ctx.onboarding_status = "pending"
                ctx.preferred_language = None
                reply_text = WELCOME_LANGUAGE_SELECTION_PROMPT

            # Step 5: Mandatory Language Selection / Onboarding Gate
            elif not ctx.is_onboarded():
                selected_lang = parse_language_selection(text)
                if selected_lang:
                    if db is not None and ctx.contact_id != "wac_dev":
                        updated = await update_contact_language(db, ctx.contact_id, selected_lang)
                        ctx.preferred_language = selected_lang
                        ctx.onboarding_status = "completed"
                    else:
                        ctx.preferred_language = selected_lang
                        ctx.onboarding_status = "completed"

                    confirmation = ctx.get_language_confirmation()
                    main_menu = ctx.get_localized_menu()
                    reply_text = f"{confirmation}\n\n{main_menu}"
                else:
                    reply_text = WELCOME_LANGUAGE_SELECTION_PROMPT

            # Step 6: Returning / Onboarded User Conversation Flow
            else:
                history = []
                if db is not None and ctx.contact_id != "wac_dev":
                    raw_history = await get_whatsapp_message_history(db, ctx.contact_id, limit=10)
                    for h in raw_history:
                        role = "user" if h.get("direction") == "inbound" else "assistant"
                        history.append({"role": role, "content": h.get("content", "")})

                intent = await detect_intent(text, ctx, media_url=inbound.media_url, history=history)
                if intent.intent == IntentType.HELP_MENU:
                    reply_text = ctx.get_localized_menu()
                elif intent.intent == IntentType.LANGUAGE_CHANGE:
                    if db is not None and ctx.contact_id != "wac_dev":
                        await reset_contact_onboarding(db, ctx.contact_id)
                    ctx.onboarding_status = "pending"
                    ctx.preferred_language = None
                    reply_text = WELCOME_LANGUAGE_SELECTION_PROMPT
                else:
                    capability_router = WhatsAppCapabilityRouter()
                    contact_dict = {"id": ctx.contact_id, "user_id": ctx.user_id, "preferred_language": ctx.preferred_language}
                    reply_text = await capability_router.route_intent(intent, history=history, db=db, contact=contact_dict)

            # Step 7: Save Outbound Response, Dispatch via Provider & Complete Reliability Claim
            if db is not None and ctx.contact_id != "wac_dev":
                await save_whatsapp_message(
                    db,
                    contact_id=ctx.contact_id,
                    direction="outbound",
                    content=reply_text,
                )
                provider_type = inbound.metadata.get("provider", "dev_simulator") if inbound.metadata else "dev_simulator"
                contact_payload = {"id": ctx.contact_id, "phone_number": inbound.from_phone, "user_id": ctx.user_id}
                await send_outbound_message(
                    db,
                    contact=contact_payload,
                    message_text=reply_text,
                    inbound_provider_message_id=provider_msg_id,
                    provider=provider_type,
                )
                await complete_message_processing(db, provider_msg_id, reply_text)

            processed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

            return SimulatedMessageResponse(
                status="ok",
                received=inbound,
                reply=reply_text,
                processed_at=processed_at,
            )
        except Exception as exc:
            if db is not None and ctx.contact_id != "wac_dev":
                await fail_message_processing(db, provider_msg_id, "INTERNAL_ERROR")
            raise exc
