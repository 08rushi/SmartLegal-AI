"""
intent.py — WhatsApp Bot Conversational Intent Model & 2-Layer Detection Engine.

Implements normalized intent classification:
1. Layer 1: Deterministic rules (100% confidence ONLY for unambiguous commands/menu digits).
   Keyword matches and attached media serve as signals without blindly forcing intent.
2. Layer 2: LLM AI Intent Classifier using canonical ai_orchestrator when Layer 1 is uncertain.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from services.whatsapp.language import (
    WhatsAppSessionContext,
    is_language_change_command,
    is_menu_command,
    LanguageCode,
)
from services.ai_provider import ai_orchestrator

logger = logging.getLogger(__name__)


class IntentType:
    LEGAL_QUESTION = "legal_question"
    DOCUMENT_ANALYSIS = "document_analysis"
    LEGAL_NOTICE = "legal_notice"
    DOCUMENT_DRAFTING = "document_drafting"
    MY_MATTERS = "my_matters"
    HELP_MENU = "help_menu"
    LANGUAGE_CHANGE = "language_change"
    UNKNOWN = "unknown"

    ALL = (
        LEGAL_QUESTION,
        DOCUMENT_ANALYSIS,
        LEGAL_NOTICE,
        DOCUMENT_DRAFTING,
        MY_MATTERS,
        HELP_MENU,
        LANGUAGE_CHANGE,
        UNKNOWN,
    )


@dataclass
class WhatsAppIntent:
    """Normalized intent model for WhatsApp messages."""

    intent: str
    confidence: float
    original_message: str
    language: str
    detection_method: str = "deterministic"  # 'deterministic' | 'ai' | 'fallback'
    metadata: Dict[str, Any] = field(default_factory=dict)


async def detect_intent(
    text: str,
    context: WhatsAppSessionContext,
    media_url: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> WhatsAppIntent:
    """
    Detect conversational intent using a 2-layer classification pipeline.
    
    Layer 1: Deterministic rule matching (1.0 confidence for explicit menu numbers, help, and language commands).
    Layer 2: Canonical LLM AI Classification via ai_orchestrator when Layer 1 is uncertain.
    """
    clean_text = text.strip() if text else ""
    cleaned_lower = clean_text.lower()
    lang = context.preferred_language if context.preferred_language in LanguageCode.ALL else LanguageCode.ENGLISH
    meta: Dict[str, Any] = {}
    if media_url:
        meta["media_url"] = media_url
        meta["has_media"] = True

    # ───────────────────────────────────────────────────────────────────────────
    # LAYER 1: Deterministic Unambiguous Commands (Confidence = 1.0)
    # ───────────────────────────────────────────────────────────────────────────

    # 1. Explicit Language Change Command
    if is_language_change_command(clean_text):
        return WhatsAppIntent(
            intent=IntentType.LANGUAGE_CHANGE,
            confidence=1.0,
            original_message=clean_text,
            language=lang,
            detection_method="deterministic",
            metadata=meta,
        )

    # 2. Explicit Menu / Help Command
    if is_menu_command(clean_text):
        return WhatsAppIntent(
            intent=IntentType.HELP_MENU,
            confidence=1.0,
            original_message=clean_text,
            language=lang,
            detection_method="deterministic",
            metadata=meta,
        )

    # 3. Unambiguous Numeric Menu Selections (1-6)
    if cleaned_lower in ("1", "1️⃣"):
        return WhatsAppIntent(
            intent=IntentType.LEGAL_QUESTION,
            confidence=1.0,
            original_message=clean_text,
            language=lang,
            detection_method="deterministic",
            metadata=meta,
        )
    if cleaned_lower in ("2", "2️⃣"):
        return WhatsAppIntent(
            intent=IntentType.DOCUMENT_ANALYSIS,
            confidence=1.0,
            original_message=clean_text,
            language=lang,
            detection_method="deterministic",
            metadata=meta,
        )
    if cleaned_lower in ("3", "3️⃣"):
        return WhatsAppIntent(
            intent=IntentType.LEGAL_NOTICE,
            confidence=1.0,
            original_message=clean_text,
            language=lang,
            detection_method="deterministic",
            metadata=meta,
        )
    if cleaned_lower in ("4", "4️⃣"):
        return WhatsAppIntent(
            intent=IntentType.DOCUMENT_DRAFTING,
            confidence=1.0,
            original_message=clean_text,
            language=lang,
            detection_method="deterministic",
            metadata=meta,
        )
    if cleaned_lower in ("5", "5️⃣"):
        return WhatsAppIntent(
            intent=IntentType.MY_MATTERS,
            confidence=1.0,
            original_message=clean_text,
            language=lang,
            detection_method="deterministic",
            metadata=meta,
        )
    if cleaned_lower in ("6", "6️⃣"):
        return WhatsAppIntent(
            intent=IntentType.HELP_MENU,
            confidence=1.0,
            original_message=clean_text,
            language=lang,
            detection_method="deterministic",
            metadata=meta,
        )

    # 4. Media-only payload without text -> Signal for document analysis
    if media_url and not clean_text:
        return WhatsAppIntent(
            intent=IntentType.DOCUMENT_ANALYSIS,
            confidence=0.9,
            original_message=clean_text,
            language=lang,
            detection_method="deterministic",
            metadata=meta,
        )

    # ───────────────────────────────────────────────────────────────────────────
    # LAYER 2: AI Classification via Canonical ai_orchestrator
    # ───────────────────────────────────────────────────────────────────────────
    try:
        ai_intent = await _classify_intent_with_ai(clean_text, lang, has_media=bool(media_url), history=history)
        if ai_intent and ai_intent.get("intent") in IntentType.ALL:
            intent_name = ai_intent["intent"]
            conf = float(ai_intent.get("confidence", 0.8))
            return WhatsAppIntent(
                intent=intent_name,
                confidence=conf,
                original_message=clean_text,
                language=lang,
                detection_method="ai",
                metadata=meta,
            )
    except Exception as exc:
        logger.warning(f"[whatsapp-intent] Layer 2 AI classification failed: {exc}.")

    # Multi-turn active conversation continuation: if history contains past legal Q&A messages (excluding onboarding selections)
    if history and len(history) >= 2:
        user_msgs = [
            m.get("content", "")
            for m in history
            if m.get("role") == "user" and m.get("content", "").strip().lower() not in ("1", "2", "3", "मराठी", "हिंदी", "english")
        ]
        if user_msgs:
            return WhatsAppIntent(
                intent=IntentType.LEGAL_QUESTION,
                confidence=0.8,
                original_message=clean_text,
                language=lang,
                detection_method="conversation_continuation",
                metadata=meta,
            )

    # Fallback to unknown if Layer 2 fails or is uncertain
    return WhatsAppIntent(
        intent=IntentType.UNKNOWN,
        confidence=0.0,
        original_message=clean_text,
        language=lang,
        detection_method="fallback",
        metadata=meta,
    )


async def _classify_intent_with_ai(
    text: str,
    language: str,
    has_media: bool = False,
    history: Optional[List[Dict[str, str]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    LLM Intent Classifier prompt executed through the canonical ai_orchestrator.
    """
    recent_context = ""
    if history:
        user_turns = [m.get("content", "") for m in history if m.get("role") == "user"][-3:]
        if user_turns:
            recent_context = f"\nRecent User Conversation Turns: {' | '.join(user_turns)}"

    prompt = f"""You are an intent classifier for SmartLegal AI (an Indian legal assistant platform).
Classify the user's message into EXACTLY one of the following normalized intent strings:

1. "legal_question" — user is asking a general legal question, seeking legal advice, rights information, or asking about a legal problem (e.g. landlord tenant dispute, deposit recovery, cheque bounce, divorce, workplace issue).
2. "document_analysis" — user wants to analyze, review, explain, or understand a document, contract, or rental agreement they have or attached.
3. "legal_notice" — user received a legal notice from a lawyer/court/landlord, or wants to respond to/understand a legal notice.
4. "document_drafting" — user wants to draft, create, or generate a new legal agreement, contract, NDA, or notice.
5. "my_matters" — user asks about their existing applications, saved matters, cases, or status.
6. "help_menu" — user is asking for the main menu, options, help, or assistance overview.
7. "language_change" — user wants to change their language setting.
8. "unknown" — input is ambiguous, a simple greeting, incoherent, or cannot be classified reliably.

User Message: "{text}"
User Saved Language: {language}
Has Attached Media File: {has_media}{recent_context}

Return ONLY valid JSON in EXACTLY this shape:
{{"intent": "<normalized_intent_string>", "confidence": 0.85}}"""

    raw_response = await ai_orchestrator.generate_completion(prompt, max_tokens=300)
    
    # Extract JSON payload
    try:
        start_idx = raw_response.find("{")
        end_idx = raw_response.rfind("}") + 1
        if start_idx != -1 and end_idx > start_idx:
            json_str = raw_response[start_idx:end_idx]
            return json.loads(json_str)
    except Exception as exc:
        logger.error(f"[whatsapp-intent] Failed to parse AI intent JSON: {exc}")
    return None
