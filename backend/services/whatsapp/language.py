"""
language.py — WhatsApp Bot Language Parsing, Session Context, and Localization.

Supports Marathi (mr), Hindi (hi), and English (en). Provides clean session
context, prompts for onboarding, and localized responses for conversation continuation.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass


class LanguageCode:
    MARATHI = "mr"
    HINDI = "hi"
    ENGLISH = "en"

    ALL = (MARATHI, HINDI, ENGLISH)


def parse_language_selection(input_text: str) -> Optional[str]:
    """
    Parse user input into a normalized language code ('mr', 'hi', 'en').
    Returns None if the input does not correspond to a supported language.
    """
    if not input_text:
        return None

    cleaned = input_text.strip().lower()

    # Marathi patterns
    if cleaned in ("1", "1️⃣", "mr", "marathi", "मराठी", "marati"):
        return LanguageCode.MARATHI

    # Hindi patterns
    if cleaned in ("2", "2️⃣", "hindi", "हिंदी", "हिन्दी", "hind"):
        return LanguageCode.HINDI

    # English patterns
    if cleaned in ("3", "3️⃣", "en", "english", "इंग्लिश", "अंग्रेजी", "इंग्रजी"):
        return LanguageCode.ENGLISH

    return None


def is_language_change_command(input_text: str) -> bool:
    """Check if the user is requesting to change their language setting in English, Hindi, or Marathi."""
    if not input_text:
        return False
    cleaned = input_text.strip().lower()

    trigger_keywords = [
        "language", "change language", "change lang", "select language", "lang",
        "bhasha", "भाषा", "भाषा बदलें", "भाषा बदला", "भाषा बदल", "भाषा बदलावी",
        "भाषा बदलणे", "reset language"
    ]
    return cleaned in trigger_keywords or any(kw in cleaned for kw in ("change language", "भाषा बदल", "भाषा बदलें"))


def is_menu_command(input_text: str) -> bool:
    """Check if the user is explicitly requesting the main menu or help."""
    if not input_text:
        return False
    cleaned = input_text.strip().lower()
    menu_triggers = {"menu", "main menu", "help", "मेनू", "मुख्य मेनू", "मदत", "सहायता", "मदद", "start", "home"}
    return cleaned in menu_triggers


WELCOME_LANGUAGE_SELECTION_PROMPT = (
    "👋 *Welcome to SmartLegal AI*\n"
    "स्मार्टलीगल एआय मध्ये आपले स्वागत आहे\n"
    "स्मार्टलीगल एआई में आपका स्वागत है\n\n"
    "I can help you understand legal issues, documents and next steps.\n\n"
    "🌐 *Select your language / आपली भाषा निवडा / अपनी भाषा चुनें:*\n\n"
    "1️⃣ Marathi (मराठी)\n"
    "2️⃣ Hindi (हिंदी)\n"
    "3️⃣ English (English)\n\n"
    "💡 _Please reply with 1, 2, or 3 (किंवा 1, 2, 3 ने उत्तर द्या)_"
)


INVALID_LANGUAGE_SELECTION_PROMPT = (
    "⚠️ *Invalid selection / अमान्य निवड / अमान्य चयन*\n\n"
    "Please choose one of the following options / कृपया एक पर्याय निवडा / कृपया एक विकल्प चुनें:\n\n"
    "1️⃣ Marathi (मराठी)\n"
    "2️⃣ Hindi (हिंदी)\n"
    "3️⃣ English (English)\n\n"
    "💡 _Reply with 1, 2, or 3_"
)


LANGUAGE_CONFIRMATION_PROMPTS = {
    LanguageCode.ENGLISH: "✅ *Language set to English!*",
    LanguageCode.HINDI: "✅ *भाषा हिंदी पर सेट की गई!*",
    LanguageCode.MARATHI: "✅ *भाषा मराठी सेट केली!*",
}


LOCALIZED_MAIN_MENU = {
    LanguageCode.ENGLISH: (
        "🌐 *SmartLegal AI — Main Menu*\n\n"
        "How can I help you today?\n\n"
        "1️⃣ Ask a legal question\n"
        "2️⃣ Analyze / understand a document\n"
        "3️⃣ Understand a legal notice\n"
        "4️⃣ Draft a legal document\n"
        "5️⃣ My matters\n"
        "6️⃣ Something else\n\n"
        "💡 _Reply with a number or type your question. Type 'language' anytime to change your language._"
    ),
    LanguageCode.HINDI: (
        "🌐 *स्मार्टलीगल एआई — मुख्य मेनू*\n\n"
        "आज मैं आपकी क्या सहायता कर सकता हूँ?\n\n"
        "1️⃣ कानूनी प्रश्न पूछें\n"
        "2️⃣ दस्तावेज़ समझें / विश्लेषण करें\n"
        "3️⃣ कानूनी नोटिस समझें\n"
        "4️⃣ कानूनी दस्तावेज़ का ड्राफ़्ट तैयार करें\n"
        "5️⃣ मेरे मामले (My Matters)\n"
        "6️⃣ कुछ और\n\n"
        "💡 _किसी नंबर का उत्तर दें या अपना प्रश्न लिखें। भाषा बदलने के लिए किसी भी समय 'भाषा' लिखें।_"
    ),
    LanguageCode.MARATHI: (
        "🌐 *स्मार्टलीगल एआय — मुख्य मेनू*\n\n"
        "आज मी तुम्हाला कशी मदत करू शकतो?\n\n"
        "1️⃣ कायदेशीर प्रश्न विचारा\n"
        "2️⃣ कागदपत्र समजून घ्या / विश्लेषण करा\n"
        "3️⃣ कायदेशीर नोटीस समजून घ्या\n"
        "4️⃣ कायदेशीर कागदपत्र तयार करा (Draft)\n"
        "5️⃣ माझे विषय (My Matters)\n"
        "6️⃣ इतर काही\n\n"
        "💡 _क्रमांकाने उत्तर द्या किंवा तुमचा प्रश्न लिहा. भाषा बदलण्यासाठी कधीही 'भाषा' टाइप करा._"
    ),
}


CONTINUATION_RESPONSES = {
    LanguageCode.ENGLISH: "Received your message: '{text}'.\n\nSmartLegal AI conversation active in English.",
    LanguageCode.HINDI: "आपका संदेश प्राप्त हुआ: '{text}'\n\nस्मार्टलीगल एआई बातचीत हिंदी में सक्रिय है।",
    LanguageCode.MARATHI: "तुमचा संदेश मिळाला: '{text}'\n\nस्मार्टलीगल एआय संवाद मराठीत सुरू आहे.",
}


def get_localized_continuation_message(language: Optional[str], text: str) -> str:
    """Get conversation continuation message in the user's preferred language."""
    lang = language if language in LanguageCode.ALL else LanguageCode.ENGLISH
    template = CONTINUATION_RESPONSES[lang]
    return template.format(text=text)


@dataclass
class WhatsAppSessionContext:
    """
    Unified conversation and language session context for a WhatsApp contact.
    """

    contact_id: str
    phone_number: str
    user_id: Optional[str] = None
    preferred_language: Optional[str] = None
    onboarding_status: str = "pending"

    def is_onboarded(self) -> bool:
        """Return True if contact has selected a valid language and completed onboarding."""
        return (
            self.onboarding_status == "completed"
            and self.preferred_language in LanguageCode.ALL
        )

    def get_localized_menu(self) -> str:
        """Return the localized main menu string based on contact's preferred language."""
        lang = self.preferred_language if self.preferred_language in LanguageCode.ALL else LanguageCode.ENGLISH
        return LOCALIZED_MAIN_MENU[lang]

    def get_language_confirmation(self) -> str:
        """Return language confirmation message."""
        lang = self.preferred_language if self.preferred_language in LanguageCode.ALL else LanguageCode.ENGLISH
        return LANGUAGE_CONFIRMATION_PROMPTS[lang]
