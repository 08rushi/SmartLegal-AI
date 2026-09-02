"""
workflow_adapter.py — WhatsApp Document Workflow Actions & Progressive Drafting Adapter.

Manages:
1. Document Risk Analysis Action (`identify_risks` / `find_key_clauses`).
2. Legal Next Steps Action (`legal_next_steps`).
3. Progressive Drafting Information Collection & Contextual "Draft it" resolution.
4. Draft Preview (`draft_ready`) & Explicit User Confirmation before final document generation.
5. Cross-user document ownership security isolation.
"""

import json
import logging
import uuid
import datetime
from typing import Dict, Any, Optional

from services.ai_provider import ai_orchestrator
from services.groq_service import LEGAL_ADVISOR_SYSTEM_PROMPT
from services.whatsapp.language import LanguageCode
from services.whatsapp.context_repository import (
    get_or_create_context,
    set_drafting_state,
    update_draft_requirements,
    clear_drafting_state,
    WorkflowState,
)
from services.whatsapp.document_analysis_adapter import (
    resolve_document_for_contact,
    answer_document_followup,
)

logger = logging.getLogger(__name__)


async def handle_risk_analysis_action(
    db: Any, contact: Dict[str, Any], language: str = LanguageCode.ENGLISH
) -> str:
    """
    Handle 'identify_risks' & 'find_key_clauses' workflow actions.
    Reuses completed analysis result or extracted document text without re-running full document analysis.
    """
    doc = await resolve_document_for_contact(db, contact)
    if not doc:
        return {
            LanguageCode.MARATHI: "❌ धोके आणि महत्त्वाच्या अटी तपासण्यासाठी आधी कागदपत्र पाठवा किंवा निवडा.",
            LanguageCode.HINDI: "❌ जोखिम और मुख्य शर्तें देखने के लिए कृपया पहले दस्तावेज़ भेजें या चुनें।",
            LanguageCode.ENGLISH: "❌ Please upload or select a document first to analyze risks and key clauses.",
        }.get(language, "❌ Please upload or select a document first to analyze risks and key clauses.")

    # Query cached analysis if available
    analysis_row = None
    if db is not None:
        analysis_row = await db.fetchrow(
            "SELECT * FROM analyses WHERE document_id = $1", doc["id"]
        )

    if analysis_row and analysis_row.get("result_json"):
        try:
            result = json.loads(analysis_row["result_json"])
            summary = result.get("summary", {})
            overall_risk = summary.get("overall_risk", "UNKNOWN").upper()
            high_risks = summary.get("high_risk_clauses", [])
            obligations = summary.get("your_obligations", [])

            risks_formatted = "\n".join([f"• {r}" for r in high_risks]) if high_risks else "• No high-risk clauses identified."
            obligations_formatted = "\n".join([f"• {o}" for o in obligations]) if obligations else "• Standard obligations apply."

            if language == LanguageCode.MARATHI:
                return (
                    f"⚠️ *कागदपत्र धोका आणि महत्त्वाच्या अटी विश्लेषण* ({doc['filename']}):\n\n"
                    f"📌 **एकूण धोका पातळी**: `{overall_risk}`\n\n"
                    f"🚨 **महत्त्वाचे धोके / उच्च जोखीम अटी**:\n{risks_formatted}\n\n"
                    f"📋 **तुमच्या मुख्य जबाबदाऱ्या**:\n{obligations_formatted}\n\n"
                    f"💡 *पुढील पावलांसाठी 'पुढे काय करू?' विचारा.*"
                )
            elif language == LanguageCode.HINDI:
                return (
                    f"⚠️ *दस्तावेज़ जोखिम और मुख्य शर्तें विश्लेषण* ({doc['filename']}):\n\n"
                    f"📌 **कुल जोखिम स्तर**: `{overall_risk}`\n\n"
                    f"🚨 **महत्वपूर्ण जोखिम / उच्च जोखिम शर्तें**:\n{risks_formatted}\n\n"
                    f"📋 **आपकी मुख्य जिम्मेदारियां**:\n{obligations_formatted}\n\n"
                    f"💡 *अगले कदमों के लिए 'आगे क्या करें?' पूछें।*"
                )

            return (
                f"⚠️ *Document Risk & Key Clause Analysis* ({doc['filename']}):\n\n"
                f"📌 **Overall Risk Level**: `{overall_risk}`\n\n"
                f"🚨 **High-Risk Clauses & Concerns**:\n{risks_formatted}\n\n"
                f"📋 **Your Key Obligations**:\n{obligations_formatted}\n\n"
                f"💡 *Type 'what should I do next?' for recommended action steps.*"
            )
        except Exception as exc:
            logger.warning(f"[whatsapp-workflow] Could not parse cached analysis: {exc}")

    # Fallback to document follow-up Q&A
    prompt = "List all high risk clauses, hidden risks, and important obligations in this document clearly."
    return await answer_document_followup(db, contact, prompt, language=language, document_id=doc["id"])


async def handle_legal_next_steps_action(
    db: Any, contact: Dict[str, Any], language: str = LanguageCode.ENGLISH
) -> str:
    """
    Handle 'legal_next_steps' workflow action ("what should I do next?").
    Provides structured guidance: Situation, Options, Recommended Step, Required Evidence, Legal Notice warning.
    """
    doc = await resolve_document_for_contact(db, contact)
    doc_label = doc["filename"] if doc else "general legal matter"

    prompt = (
        f"Provide practical legal next steps for the user regarding their {doc_label}.\n"
        "Format as:\n"
        "1. Situation Summary\n"
        "2. Possible Legal Options\n"
        "3. Recommended Next Step\n"
        "4. Evidence/Documents Needed\n"
        "5. When to Consult an Advocate\n"
        "Keep response under 300 words, highly practical and mobile-friendly."
    )

    if doc and db is not None:
        analysis_row = await db.fetchrow(
            "SELECT * FROM analyses WHERE document_id = $1", doc["id"]
        )
        if analysis_row and analysis_row.get("result_json"):
            return await answer_document_followup(db, contact, prompt, language=language, document_id=doc["id"])

    # General / Fallback legal next steps via canonical ai_orchestrator
    messages = [
        {"role": "system", "content": LEGAL_ADVISOR_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    return await ai_orchestrator.generate_chat_completion(messages, max_tokens=1200)


async def handle_drafting_workflow(
    db: Any,
    contact: Dict[str, Any],
    user_message: str,
    language: str = LanguageCode.ENGLISH,
) -> str:
    """
    Handle progressive drafting information collection and draft preview generation.
    """
    contact_id = contact["id"]
    ctx = await get_or_create_context(db, contact_id)
    doc = await resolve_document_for_contact(db, contact)

    # 1. Resolve draft requirements stored in context
    raw_reqs = ctx.get("draft_requirements_json", "{}")
    try:
        reqs = json.loads(raw_reqs)
    except Exception:
        reqs = {}

    draft_type = ctx.get("draft_type") or "legal_notice"

    # Pre-populate facts from active document analysis if available & not yet stored
    if doc and db is not None:
        analysis_row = await db.fetchrow("SELECT * FROM analyses WHERE document_id = $1", doc["id"])
        if analysis_row and analysis_row.get("result_json"):
            try:
                res_data = json.loads(analysis_row["result_json"])
                summary = res_data.get("summary", {})
                if "parties" in summary and not reqs.get("parties"):
                    reqs["parties"] = ", ".join(summary["parties"])
                if "doc_name" not in reqs:
                    reqs["doc_name"] = doc["filename"]
            except Exception:
                pass

    # Update requirements with latest user message if in awaiting_drafting_input state
    if ctx.get("workflow_state") == WorkflowState.AWAITING_DRAFTING_INPUT:
        if "recipient" not in reqs:
            reqs["recipient"] = user_message.strip()
        elif "purpose" not in reqs:
            reqs["purpose"] = user_message.strip()

    # 2. Check for missing required information
    if "recipient" not in reqs:
        await set_drafting_state(db, contact_id, draft_type, reqs, workflow_state=WorkflowState.AWAITING_DRAFTING_INPUT)
        if language == LanguageCode.MARATHI:
            return "📝 **मसुदा तयार करणे**: हा नोटीस/मसुदा कोणाला पाठवायचा आहे? (उदा. घरमालक / कंपनी / व्यक्तीचे नाव)."
        elif language == LanguageCode.HINDI:
            return "📝 **ड्राफ्ट बनाना**: यह नोटिस/ड्राफ्ट किसे भेजना है? (जैसे मकान मालिक / कंपनी / व्यक्ति का नाम)।"
        return "📝 **Draft Preparation**: Who should this notice/draft be addressed to? (e.g. Landlord name / Company / Party name)."

    if "purpose" not in reqs:
        await set_drafting_state(db, contact_id, draft_type, reqs, workflow_state=WorkflowState.AWAITING_DRAFTING_INPUT)
        if language == LanguageCode.MARATHI:
            return "📝 **मसुदा तयार करणे**: नोटीस पाठवण्याचे मुख्य कारण किंवा मागणी काय आहे? (उदा. डिपॉझिट परत करणे / कराराचे पालन / थकबाकी)."
        elif language == LanguageCode.HINDI:
            return "📝 **ड्राफ्ट बनाना**: नोटिस भेजने का मुख्य कारण या मांग क्या है? (जैसे डिपॉजिट वापसी / अनुबंध पालन / बकाया राशि)।"
        return "📝 **Draft Preparation**: What is the main reason or demand for this notice? (e.g. Refund of security deposit / Rent payment / Contract compliance)."

    # 3. All required information present -> Generate Draft Preview & set state = draft_ready
    await set_drafting_state(
        db,
        contact_id,
        draft_type,
        reqs,
        workflow_state=WorkflowState.DRAFT_READY,
        confirmation_status="awaiting_confirmation",
    )

    recipient = reqs.get("recipient", "Opposing Party")
    purpose = reqs.get("purpose", "Demand & Legal Notice")
    doc_ref = f" (Based on `{doc['filename']}`)" if doc else ""

    if language == LanguageCode.MARATHI:
        return (
            f"📋 *कायदेशीर नोटीस मसुदा पूर्वदृश्य*{doc_ref}:\n\n"
            f"• **प्रकार**: `लीगल नोटीस ({draft_type})`\n"
            f"• **प्राप्तकर्ता**: `{recipient}`\n"
            f"• **उद्देश/मागणी**: `{purpose}`\n\n"
            f"कृपया अंतिम मसुदा तयार करण्यासाठी खालील पर्याय निवडा:\n"
            f"1. अंतिम मसुदा तयार करा (Finalize & Store)\n"
            f"2. माहिती बदला (Make changes)\n"
            f"3. मसुदा रद्द करा (Cancel)\n\n"
            f"उत्तर देण्यासाठी `1` किंवा `रद्द` लिहा."
        )
    elif language == LanguageCode.HINDI:
        return (
            f"📋 *कानूनी नोटिस ड्राफ्ट पूर्वावलोकन*{doc_ref}:\n\n"
            f"• **प्रकार**: `लीगल नोटिस ({draft_type})`\n"
            f"• **प्राप्तकर्ता**: `{recipient}`\n"
            f"• **उद्देश/मांग**: `{purpose}`\n\n"
            f"कृपया अंतिम ड्राफ्ट बनाने के लिए विकल्प चुनें:\n"
            f"1. अंतिम ड्राफ्ट बनाएं (Finalize & Store)\n"
            f"2. विवरण बदलें (Make changes)\n"
            f"3. ड्राफ्ट रद्द करें (Cancel)\n\n"
            f"उत्तर देने के लिए `1` या `रद्द` लिखें।"
        )

    return (
        f"📋 *Legal Notice Draft Preview*{doc_ref}:\n\n"
        f"• **Type**: `Legal Notice ({draft_type})`\n"
        f"• **Recipient**: `{recipient}`\n"
        f"• **Purpose/Demand**: `{purpose}`\n\n"
        f"Please confirm to finalize and generate the draft:\n"
        f"1. Generate Final Document\n"
        f"2. Make Changes\n"
        f"3. Cancel Draft\n\n"
        f"Reply with `1` or `YES` to confirm."
    )


async def handle_draft_confirmation(
    db: Any, contact: Dict[str, Any], user_input: str, language: str = LanguageCode.ENGLISH
) -> str:
    """
    Handle explicit user confirmation choice when in draft_ready state.
    Option '1' / 'YES' -> Finalizes draft & registers document record.
    Option '3' / 'CANCEL' -> Clears drafting state.
    """
    contact_id = contact["id"]
    user_id = contact.get("user_id") or contact_id
    ctx = await get_or_create_context(db, contact_id)
    text_lower = user_input.strip().lower()

    # Option 3 or Cancel -> Cancel draft
    if text_lower in ("3", "cancel", "stop", "रद्द", "रद्द करा", "रद्द करें"):
        await clear_drafting_state(db, contact_id)
        return {
            LanguageCode.MARATHI: "❌ मसुदा तयार करणे रद्द केले आहे.",
            LanguageCode.HINDI: "❌ ड्राफ्ट बनाना रद्द कर दिया गया है।",
            LanguageCode.ENGLISH: "❌ Legal draft creation cancelled.",
        }.get(language, "❌ Legal draft creation cancelled.")

    # Option 1 or Confirmation -> Generate Final Document
    if text_lower in ("1", "yes", "confirm", "ho", "हाँ", "होय"):
        raw_reqs = ctx.get("draft_requirements_json", "{}")
        try:
            reqs = json.loads(raw_reqs)
        except Exception:
            reqs = {}

        draft_type = ctx.get("draft_type", "legal_notice")
        recipient = reqs.get("recipient", "Opposing Party")
        purpose = reqs.get("purpose", "Legal demand")

        # Generate complete legal draft text via canonical ai_orchestrator
        system_prompt = LEGAL_ADVISOR_SYSTEM_PROMPT
        user_prompt = (
            f"Draft a formal, professional Legal Notice under Indian Law.\n"
            f"Recipient: {recipient}\n"
            f"Demand/Purpose: {purpose}\n"
            f"Format as a complete, ready-to-send legal notice with Advocates signature block."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        final_draft_text = await ai_orchestrator.generate_chat_completion(messages, max_tokens=1800)

        # Register finalized document in 'documents' table
        doc_id = f"doc_draft_{uuid.uuid4().hex[:10]}"
        filename = f"Legal_Notice_{draft_type}_{uuid.uuid4().hex[:4]}.txt"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if db is not None:
            await db.execute(
                """
                INSERT INTO documents (
                    id, user_id, filename, file_url, file_size, document_type, status, uploaded_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                doc_id, user_id, filename, f"text://{filename}", len(final_draft_text), "text/plain", "ready", now_iso
            )

        # Clear temporary drafting state
        await clear_drafting_state(db, contact_id)

        if language == LanguageCode.MARATHI:
            return (
                f"✅ *अंतिम लीगल नोटीस मसुदा यशस्वीपणे तयार झाला आहे!*\n\n"
                f"📄 **फाइल नाव**: `{filename}`\n\n"
                f"```text\n{final_draft_text[:800]}...\n```\n\n"
                f"💡 *टीप: हा मसुदा तुमच्या खात्यात जतन केला गेला आहे.*"
            )
        elif language == LanguageCode.HINDI:
            return (
                f"✅ *अंतिम लीगल नोटिस ड्राफ्ट सफलतापूर्वक तैयार हो गया है!*\n\n"
                f"📄 **फ़ाइल का नाम**: `{filename}`\n\n"
                f"```text\n{final_draft_text[:800]}...\n```\n\n"
                f"💡 *नोट: यह ड्राफ्ट आपके खाते में सुरक्षित कर दिया गया है।*"
            )

        return (
            f"✅ *Final Legal Notice Draft Generated Successfully!*\n\n"
            f"📄 **Document File**: `{filename}`\n\n"
            f"```text\n{final_draft_text[:800]}...\n```\n\n"
            f"💡 *Note: Finalized draft has been registered in your account.*"
        )

    # Invalid choice in draft_ready state -> return localized prompt (do NOT call LLM)
    return {
        LanguageCode.MARATHI: "कृपया मसुदा अंतिम करण्यासाठी `1` किंवा रद्द करण्यासाठी `3` लिहून उत्तर द्या.",
        LanguageCode.HINDI: "कृपया ड्राफ्ट को अंतिम रूप देने के लिए `1` या रद्द करने के लिए `3` लिखकर उत्तर दें।",
        LanguageCode.ENGLISH: "Please reply with `1` to generate the final document or `3` to cancel.",
    }.get(language, "Please reply with `1` to generate the final document or `3` to cancel.")
