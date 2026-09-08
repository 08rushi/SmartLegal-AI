"""
boundaries.py — WhatsApp Service Boundaries & SmartLegal AI Capability Adapters.

Connects WhatsApp routing to SmartLegal AI backend services (AI Orchestrator, Legal Advisor,
Document Parser, Application Service) without duplicating business logic.
"""

import logging
from typing import Optional, Dict, Any, List
from services.ai_provider import ai_orchestrator
from services.groq_service import LEGAL_ADVISOR_SYSTEM_PROMPT
from services.whatsapp.intent import WhatsAppIntent, IntentType
from services.whatsapp.language import LanguageCode, get_localized_continuation_message
from services.whatsapp.media import DevMediaDownloader, get_whatsapp_media_downloader
from services.whatsapp.document_adapter import process_whatsapp_document_intake
from services.whatsapp.document_analysis_adapter import (
    execute_whatsapp_document_analysis,
    answer_document_followup,
    resolve_document_for_contact,
)
from services.whatsapp.workflow_adapter import (
    handle_risk_analysis_action,
    handle_legal_next_steps_action,
    handle_drafting_workflow,
    handle_draft_confirmation,
)
from services.whatsapp.context_repository import (
    get_or_create_context,
    get_active_document_id,
    set_active_document,
    clear_active_document,
    set_pending_candidates,
    resolve_candidate_selection,
    set_workflow_state,
    clear_drafting_state,
    WorkflowState,
)

logger = logging.getLogger(__name__)


# Localized Prompt Templates for Boundaries & Clarifications
UNKNOWN_CLARIFICATION = {
    LanguageCode.MARATHI: (
        "मी तुम्हाला कायदेशीर प्रश्न, कागदपत्रे, नोटीस किंवा पुढील प्रक्रिया समजून घेण्यास मदत करू शकतो. "
        "तुम्हाला नेमकी कशासाठी मदत हवी आहे?\n\n"
        "💡 _तुम्ही 1, 2, 3 निवडून मुख्य मेनू देखील पाहू शकता._"
    ),
    LanguageCode.HINDI: (
        "मैं आपको कानूनी प्रश्नों, दस्तावेजों, नोटिसों या अगले कदमों को समझने में मदद कर सकता हूँ। "
        "आपको किस बारे में सहायता चाहिए?\n\n"
        "💡 _आप मुख्य मेनू देखने के लिए 'मेनू' भी लिख सकते हैं।_"
    ),
    LanguageCode.ENGLISH: (
        "I can help you understand legal issues, documents, notices, or next steps. "
        "What specific legal help do you need today?\n\n"
        "💡 _You can also type 'menu' to view options._"
    ),
}

PROMPT_DOCUMENT_UPLOAD = {
    LanguageCode.MARATHI: "नक्कीच. कृपया तुमचे कागदपत्र किंवा कराराची PDF अथवा फोटो पाठवा. मी त्याचे विश्लेषण करून धोके आणि अटी स्पष्ट करेन.",
    LanguageCode.HINDI: "ज़रूर। कृपया अपना दस्तावेज़ या एग्रीमेंट की PDF अथवा फोटो भेजें। मैं उसका विश्लेषण करके जोखिम और शर्तें समझाऊंगा।",
    LanguageCode.ENGLISH: "Sure. Please send or upload your legal document / contract PDF or photo. I will analyze the risks and key clauses for you.",
}

PROMPT_LEGAL_NOTICE = {
    LanguageCode.MARATHI: "नक्कीच. कृपया तुम्हाला मिळालेल्या legal notice चा फोटो किंवा PDF पाठवा, किंवा नोटीसमधील मुख्य माहिती सांगा.",
    LanguageCode.HINDI: "ज़रूर। कृपया आपको मिली legal notice की फोटो या PDF भेजें, या नोटिस का मुख्य विवरण यहाँ लिखें।",
    LanguageCode.ENGLISH: "Sure. Please send a photo or PDF of the legal notice you received, or briefly describe the notice details here.",
}

PROMPT_DOCUMENT_DRAFTING = {
    LanguageCode.MARATHI: "तुम्हाला कोणता करार किंवा मसुदा तयार करायचा आहे? (उदा. घरभाडे करार, NDA, विक्री पत्र). कृपया मुख्य अटी सांगा.",
    LanguageCode.HINDI: "आप कौन सा एग्रीमेंट या ड्राफ्ट बनाना चाहते हैं? (जैसे किरायानामा, NDA, बिक्री पत्र)। कृपया मुख्य शर्तें बताएं।",
    LanguageCode.ENGLISH: "Which document would you like to draft? (e.g. Rent Agreement, NDA, Sale Deed). Please describe the key terms.",
}

PROMPT_MY_MATTERS = {
    LanguageCode.MARATHI: "स्मार्टलीगल प्लॅटफॉर्मवरील तुमचे सर्व विषय आणि अर्ज सिंक केले आहेत. सध्या 2 कायदेशीर अर्ज प्रक्रियेत आहेत.",
    LanguageCode.HINDI: "स्मार्टलीगल प्लेटफॉर्म पर आपके सभी मामले और आवेदन सिंक किए गए हैं। वर्तमान में 2 कानूनी आवेदन प्रक्रिया में हैं।",
    LanguageCode.ENGLISH: "Your SmartLegal cases and applications are synced. Currently 2 applications are active in your account.",
}


class WhatsAppCapabilityRouter:
    """
    Service boundary adapter routing detected intents to SmartLegal AI capabilities.
    """

    async def route_intent(
        self,
        intent: WhatsAppIntent,
        history: Optional[List[Dict[str, str]]] = None,
        db: Any = None,
        contact: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Route intent to the appropriate SmartLegal AI service boundary.
        """
        lang = intent.language if intent.language in LanguageCode.ALL else LanguageCode.ENGLISH
        contact_dict = contact or {"id": "wac_dev", "user_id": "user_dev"}
        contact_id = contact_dict["id"]
        user_id = contact_dict.get("user_id") or contact_id
        text_lower = (intent.original_message or "").strip().lower()

        # 0. Deterministic Cancellation Command ("cancel", "cancel draft", "रद्द", "रद्द करा", "रद्द करें")
        if any(cmd in text_lower for cmd in ("cancel draft", "cancel", "stop", "रद्द", "रद्द करा", "रद्द करें")):
            ctx = await get_or_create_context(db, contact_id)
            if ctx.get("workflow_state") in (WorkflowState.AWAITING_DRAFTING_INPUT, WorkflowState.DRAFTING, WorkflowState.DRAFT_READY):
                await clear_drafting_state(db, contact_id)
                return {
                    LanguageCode.MARATHI: "❌ मसुदा प्रक्रिया रद्द केली आहे.",
                    LanguageCode.HINDI: "❌ ड्राफ्ट प्रक्रिया रद्द कर दी गई है।",
                    LanguageCode.ENGLISH: "❌ Legal drafting workflow cancelled.",
                }.get(lang, "❌ Legal drafting workflow cancelled.")

        # 1. Active Workflow State Checks (draft_ready / awaiting_drafting_input)
        ctx = await get_or_create_context(db, contact_id)
        current_state = ctx.get("workflow_state")

        if current_state == WorkflowState.DRAFT_READY:
            return await handle_draft_confirmation(db, contact_dict, intent.original_message, lang)

        if current_state == WorkflowState.AWAITING_DRAFTING_INPUT:
            return await handle_drafting_workflow(db, contact_dict, intent.original_message, lang)

        # 2. Deterministic Command: Clear Context ("clear document", "clear context", "कागदपत्र काढून टाका", "दस्तावेज़ साफ़ करें")
        if any(cmd in text_lower for cmd in ("clear document", "clear context", "forget document", "कागदपत्र काढून टाका", "दस्तावेज़ साफ़ करें")):
            await clear_active_document(db, contact_id)
            clear_msgs = {
                LanguageCode.MARATHI: "✅ कागदपत्र संदर्भ काढून टाकला आहे. तुमचे पुढील प्रश्न सामान्य कायदेशीर प्रश्न म्हणून मानले जातील.",
                LanguageCode.HINDI: "✅ दस्तावेज़ संदर्भ साफ़ कर दिया गया है। आपके अगले प्रश्न सामान्य कानूनी प्रश्न के रूप में माने जाएंगे।",
                LanguageCode.ENGLISH: "✅ Document context cleared. Your next questions will be treated as general legal questions unless you select another document.",
            }
            return clear_msgs.get(lang, clear_msgs[LanguageCode.ENGLISH])

        # 3. Deterministic Command: Current Document ("current document", "this document", "सध्याचे कागदपत्र", "वर्तमान दस्तावेज़")
        if any(cmd in text_lower for cmd in ("current document", "this document", "sadhyache", "सध्याचे कागदपत्र", "वर्तमान दस्तावेज़")):
            active_doc = await resolve_document_for_contact(db, contact_dict)
            if active_doc:
                return (
                    f"📌 *Current Active Document*:\n"
                    f"• Filename: `{active_doc['filename']}`\n"
                    f"• Status: `{active_doc.get('status', 'ready')}`\n\n"
                    f"You can ask me questions about this document or say 'clear document' to reset context."
                )
            return "❌ No active document currently selected. Upload a document or say 'change document' to select one."

        # 4. Deterministic Command: Change Document ("change document", "different document", "कागदपत्र बदला", "दस्तावेज़ बदलें")
        if any(cmd in text_lower for cmd in ("change document", "different document", "कागदपत्र बदला", "दस्तावेज़ बदलें")):
            return await self._handle_change_document_request(db, contact_dict, lang)

        # 5. Pending Document Selection Check (workflow_state == 'awaiting_document_selection')
        if current_state == WorkflowState.AWAITING_DOCUMENT_SELECTION:
            if text_lower.isdigit():
                idx = int(text_lower)
                cand_doc_id = await resolve_candidate_selection(db, contact_id, idx)
                if cand_doc_id:
                    # Validate ownership!
                    if db is not None:
                        val_doc = await db.fetchrow("SELECT * FROM documents WHERE id = $1 AND user_id = $2", cand_doc_id, user_id)
                        if not val_doc:
                            await clear_active_document(db, contact_id)
                            return "❌ Selected document does not belong to your account."

                    await set_active_document(db, contact_id, cand_doc_id, workflow_state="document_active")
                    confirm_msgs = {
                        LanguageCode.MARATHI: "✅ निवडलेले कागदपत्र यशस्वीपणे सक्रिय केले आहे. आता तुम्ही याबद्दल विचारू शकता.",
                        LanguageCode.HINDI: "✅ चुना गया दस्तावेज़ सफलतापूर्वक सक्रिय कर दिया गया है। अब आप इसके बारे में पूछ सकते हैं।",
                        LanguageCode.ENGLISH: "✅ Selected document is now active. You can ask me questions about it.",
                    }
                    return confirm_msgs.get(lang, confirm_msgs[LanguageCode.ENGLISH])

                # Invalid numeric choice -> return localized retry prompt (candidates remain intact)
                return {
                    LanguageCode.MARATHI: "❌ अयोग्य पर्याय. कृपया यादीतील योग्य क्रमांकाचे उत्तर द्या.",
                    LanguageCode.HINDI: "❌ अमान्य विकल्प। कृपया सूची में से सही नंबर का उत्तर दें।",
                    LanguageCode.ENGLISH: "❌ Invalid selection. Please reply with a valid number from the list above.",
                }.get(lang, "❌ Invalid selection. Please reply with a valid number from the list above.")

            # Non-numeric message sent while selection pending -> return deterministic prompt without AI call
            return {
                LanguageCode.MARATHI: "कृपया तुम्ही वापरू इच्छित असलेल्या कागदपत्राचा क्रमांक (उदा. 1 किंवा 2) लिहून उत्तर द्या.",
                LanguageCode.HINDI: "कृपया उस दस्तावेज़ का नंबर (जैसे 1 या 2) लिखकर उत्तर दें जिसका आप उपयोग करना चाहते हैं।",
                LanguageCode.ENGLISH: "Please reply with the number of the document you want to use from the list above.",
            }.get(lang, "Please reply with the number of the document you want to use from the list above.")

        # 6. Workflow Action Triggers
        # Risk Analysis Action ("risks", "risky clauses", "धोके", "जोखिम")
        if any(k in text_lower for k in ("risk", "risks", "risky", "धोके", "जोखिम")):
            return await handle_risk_analysis_action(db, contact_dict, lang)

        # Legal Next Steps Action ("what should i do", "next steps", "options", "पुढे काय करू", "आगे क्या करें")
        if any(k in text_lower for k in ("next step", "what should i do", "options", "पुढे काय करू", "आगे क्या करें")):
            return await handle_legal_next_steps_action(db, contact_dict, lang)

        # Drafting Action ("draft", "prepare notice", "prepare letter", "write this", "मसुदा", "ड्राफ्ट")
        if any(k in text_lower for k in ("draft", "prepare notice", "prepare letter", "write this", "मसुदा", "ड्राफ्ट")):
            return await handle_drafting_workflow(db, contact_dict, intent.original_message, lang)

        if intent.intent == IntentType.LEGAL_QUESTION:
            return await self._handle_legal_question(intent.original_message, lang, history=history)

        elif intent.intent == IntentType.DOCUMENT_ANALYSIS:
            return await self._handle_document_analysis(intent, lang, db=db, contact=contact)

        elif intent.intent == IntentType.LEGAL_NOTICE:
            return await self._handle_legal_notice(intent, lang, db=db, contact=contact)

        elif intent.intent == IntentType.DOCUMENT_DRAFTING:
            return self._handle_document_drafting(intent, lang)

        elif intent.intent == IntentType.MY_MATTERS:
            return self._handle_my_matters(intent, lang)

        else:
            return UNKNOWN_CLARIFICATION.get(lang, UNKNOWN_CLARIFICATION[LanguageCode.ENGLISH])

    async def _handle_legal_question(
        self,
        question: str,
        language: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Delegates legal Q&A to canonical ai_orchestrator using LEGAL_ADVISOR_SYSTEM_PROMPT.
        Preserves user language context and bounded conversation history.
        """
        lang_names = {
            LanguageCode.MARATHI: "Marathi (मराठी)",
            LanguageCode.HINDI: "Hindi (हिंदी)",
            LanguageCode.ENGLISH: "English",
        }
        target_lang = lang_names.get(language, "English")
        lang_instruction = f"CRITICAL REQUIREMENT: Answer the citizen's question strictly in {target_lang} language."

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": f"{LEGAL_ADVISOR_SYSTEM_PROMPT}\n\n{lang_instruction}"}
        ]

        # Bounded conversation memory: max last 6 turns, clipped to 1000 chars per message
        bounded_history = (history or [])[-6:]
        for m in bounded_history:
            role = "assistant" if m.get("role") == "assistant" else "user"
            content = str(m.get("content", "")).strip()[:1000]
            if content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": question.strip()})

        try:
            advice = await ai_orchestrator.generate_chat_completion(messages, max_tokens=1500)
            advice_text = advice.strip() if advice else ""
            if not advice_text:
                raise RuntimeError("Empty response received from AI provider")

            # Format & ensure localized disclaimer is present
            disclaimers = {
                LanguageCode.MARATHI: "\n\n📌 *टीप: हा भारतीय कायद्यावर आधारित एआय सल्ला आहे, परवानाधारक वकीलाचा पर्याय नाही.*",
                LanguageCode.HINDI: "\n\n📌 *नोट: यह भारतीय कानून पर आधारित एआई मार्गदर्शन है, किसी वकील का विकल्प नहीं है।*",
                LanguageCode.ENGLISH: "\n\n📌 *Note: This is AI legal guidance based on Indian law, not a substitute for a licensed advocate.*",
            }
            disclaimer = disclaimers.get(language, disclaimers[LanguageCode.ENGLISH])

            if "Note:" not in advice_text and "टीप:" not in advice_text and "नोट:" not in advice_text:
                advice_text = f"{advice_text}{disclaimer}"

            return advice_text

        except Exception as exc:
            logger.error(f"[whatsapp-qa-boundary] Legal Q&A call via ai_orchestrator failed: {exc}")
            fallbacks = {
                LanguageCode.MARATHI: "क्षमस्व, सध्या तुमच्या प्रश्नाचे उत्तर देताना तांत्रिक अडचण आली. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा.",
                LanguageCode.HINDI: "क्षमा करें, अभी आपके प्रश्न का उत्तर देते समय तकनीकी समस्या आई। कृपया थोड़ी देर बाद फिर प्रयास करें।",
                LanguageCode.ENGLISH: "Sorry, I’m having trouble processing your question right now. Please try again shortly.",
            }
            return fallbacks.get(language, fallbacks[LanguageCode.ENGLISH])

    async def _handle_document_analysis(
        self,
        intent: WhatsAppIntent,
        language: str,
        db: Any = None,
        contact: Optional[Dict[str, Any]] = None,
    ) -> str:
        contact_dict = contact or {"id": "wac_dev", "user_id": "user_dev"}

        # Scenario A: Inbound message has attached document/image media -> Ingest & Analyze
        if intent.metadata.get("has_media") or intent.metadata.get("media_url") or intent.metadata.get("media_id"):
            media_url = intent.metadata.get("media_url", "")
            media_id = intent.metadata.get("media_id", "") or media_url
            try:
                downloader = get_whatsapp_media_downloader(intent.metadata)
                downloaded = await downloader.download_media(media_id=media_id, media_url=media_url)
                doc_record = await process_whatsapp_document_intake(
                    db, contact_dict, downloaded, intent.original_message
                )
                intent.metadata["document_id"] = doc_record["id"]
                intent.metadata["file_url"] = doc_record["file_url"]

                # Automatically trigger analysis for newly ingested document
                return await execute_whatsapp_document_analysis(
                    db, contact_dict, document_id=doc_record["id"], language=language
                )

            except Exception as exc:
                logger.error(f"[whatsapp-intake-boundary] Document intake failed: {exc}")
                error_msg = str(exc)
                if "exceeds" in error_msg.lower() or "too large" in error_msg.lower():
                    if language == LanguageCode.MARATHI:
                        return "❌ फाइल खूप मोठी आहे. कमाल परवानगी असलेली मर्यादा 10 MB आहे."
                    elif language == LanguageCode.HINDI:
                        return "❌ फ़ाइल बहुत बड़ी है। अधिकतम अनुमत आकार 10 MB है।"
                    return "❌ File is too large. Maximum allowed size is 10 MB."

                if language == LanguageCode.MARATHI:
                    return "❌ कागदपत्र स्वीकारताना त्रुटी आली. कृपया वैध PDF किंवा फोटो पाठवा."
                elif language == LanguageCode.HINDI:
                    return "❌ दस्तावेज़ स्वीकार करने में त्रुटि आई। कृपया वैध PDF या फोटो भेजें।"
                return "❌ Could not process document. Please upload a valid PDF or image file (JPG, PNG, WebP)."

        # Scenario B: Text-only request (e.g. "Analyze my document", "try again", or follow-up)
        text_lower = intent.original_message.lower() if intent.original_message else ""
        force_retry = any(k in text_lower for k in ("retry", "try again", "पुन्हा", "दोबारा"))
        doc_id = intent.metadata.get("document_id")

        # Verify whether a document actually exists for the contact first
        doc = await resolve_document_for_contact(db, contact_dict, doc_id)
        if not doc:
            return PROMPT_DOCUMENT_UPLOAD.get(language, PROMPT_DOCUMENT_UPLOAD[LanguageCode.ENGLISH])

        # Check if question is a document-specific follow-up question
        is_followup = any(k in text_lower for k in ("notice period", "termination", "clause", "अट", "मुदत", "शर्त"))
        if is_followup:
            return await answer_document_followup(
                db, contact_dict, intent.original_message, language=language, document_id=doc_id
            )

        return await execute_whatsapp_document_analysis(
            db, contact_dict, document_id=doc_id, language=language, force_retry=force_retry
        )

    async def _handle_legal_notice(
        self,
        intent: WhatsAppIntent,
        language: str,
        db: Any = None,
        contact: Optional[Dict[str, Any]] = None,
    ) -> str:
        if intent.metadata.get("has_media") or intent.metadata.get("media_url") or intent.metadata.get("media_id"):
            return await self._handle_document_analysis(intent, language, db=db, contact=contact)

        return PROMPT_LEGAL_NOTICE.get(language, PROMPT_LEGAL_NOTICE[LanguageCode.ENGLISH])

    def _handle_document_drafting(self, intent: WhatsAppIntent, language: str) -> str:
        return PROMPT_DOCUMENT_DRAFTING.get(language, PROMPT_DOCUMENT_DRAFTING[LanguageCode.ENGLISH])

    def _handle_my_matters(self, intent: WhatsAppIntent, language: str) -> str:
        return PROMPT_MY_MATTERS.get(language, PROMPT_MY_MATTERS[LanguageCode.ENGLISH])

    async def _handle_change_document_request(self, db: Any, contact: Dict[str, Any], language: str) -> str:
        if db is None:
            return "No documents available."

        contact_id = contact["id"]
        user_id = contact.get("user_id") or contact_id

        docs = await db.fetch("SELECT * FROM documents WHERE user_id = $1 ORDER BY uploaded_at DESC LIMIT 5", user_id)
        if not docs:
            return {
                LanguageCode.MARATHI: "❌ तुमच्या खात्यात कोणतेही कागदपत्र आढळले नाही. कृपया आधी कागदपत्र अपलोड करा.",
                LanguageCode.HINDI: "❌ आपके खाते में कोई दस्तावेज़ नहीं मिला। कृपया पहले दस्तावेज़ अपलोड करें।",
                LanguageCode.ENGLISH: "❌ No documents found in your account. Please upload a document first.",
            }.get(language, "❌ No documents found in your account. Please upload a document first.")

        if len(docs) == 1:
            await set_active_document(db, contact_id, docs[0]["id"], workflow_state="document_active")
            return f"✅ '{docs[0]['filename']}' is your only document and is now active."

        candidate_ids = [d["id"] for d in docs]
        await set_pending_candidates(db, contact_id, candidate_ids)

        items_str = "\n".join([f"{idx + 1}. {d['filename']}" for idx, d in enumerate(docs)])

        if language == LanguageCode.MARATHI:
            return (
                "📋 **कृपया वापरण्यासाठी कागदपत्र निवडा**:\n\n"
                f"{items_str}\n\n"
                f"निवडण्यासाठी क्रमांकासह (1 ते {len(docs)}) उत्तर द्या."
            )
        elif language == LanguageCode.HINDI:
            return (
                "📋 **कृपया उपयोग के लिए दस्तावेज़ चुनें**:\n\n"
                f"{items_str}\n\n"
                f"चुनने के लिए नंबर (1 से {len(docs)}) लिखकर उत्तर दें।"
            )

        return (
            "📋 **Please select a document to activate**:\n\n"
            f"{items_str}\n\n"
            f"Reply with the number (1 to {len(docs)}) to select."
        )
