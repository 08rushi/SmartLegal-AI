"""
Central catalog of user-visible backend messages (HTTPException detail strings and
error payloads) in English / Hindi / Marathi.

Routers keep raising English ``detail`` strings (stable for logs/tests/clients that
match on them). A global exception handler in ``main.py`` calls ``translate_message``
with the language from the ``X-Lang`` header; strings that are not in the catalog pass
through unchanged. Dynamic messages (with ids/limits) are matched by ``PATTERNS``.
"""

from __future__ import annotations

import re
from typing import Optional

from services.lang import normalize_lang

# English -> {"hi": ..., "mr": ...}
MESSAGES: dict[str, dict[str, str]] = {
    # ── documents / ownership ────────────────────────────────────────────────
    "Document not found": {"hi": "दस्तावेज़ नहीं मिला।", "mr": "दस्तऐवज सापडला नाही."},
    "Document not found.": {"hi": "दस्तावेज़ नहीं मिला।", "mr": "दस्तऐवज सापडला नाही."},
    "You do not have permission to chat on this document.": {
        "hi": "आपको इस दस्तावेज़ पर चैट करने की अनुमति नहीं है।",
        "mr": "तुम्हाला या दस्तऐवजावर चॅट करण्याची परवानगी नाही."},
    "You do not have permission to access this document's chat history.": {
        "hi": "आपको इस दस्तावेज़ की चैट हिस्ट्री देखने की अनुमति नहीं है।",
        "mr": "तुम्हाला या दस्तऐवजाचा चॅट इतिहास पाहण्याची परवानगी नाही."},
    "You do not have permission to access this document.": {
        "hi": "आपको इस दस्तावेज़ तक पहुँचने की अनुमति नहीं है।",
        "mr": "तुम्हाला या दस्तऐवजापर्यंत पोहोचण्याची परवानगी नाही."},
    "You do not have permission to analyze this document.": {
        "hi": "आपको इस दस्तावेज़ का विश्लेषण करने की अनुमति नहीं है।",
        "mr": "तुम्हाला या दस्तऐवजाचे विश्लेषण करण्याची परवानगी नाही."},
    "You do not have permission to delete this document's cache.": {
        "hi": "आपको इस दस्तावेज़ का कैश हटाने की अनुमति नहीं है।",
        "mr": "तुम्हाला या दस्तऐवजाचा कॅश हटवण्याची परवानगी नाही."},
    "You do not have permission to delete this document.": {
        "hi": "आपको इस दस्तावेज़ को हटाने की अनुमति नहीं है।",
        "mr": "तुम्हाला हा दस्तऐवज हटवण्याची परवानगी नाही."},
    "You do not have permission to download this document.": {
        "hi": "आपको इस दस्तावेज़ को डाउनलोड करने की अनुमति नहीं है।",
        "mr": "तुम्हाला हा दस्तऐवज डाउनलोड करण्याची परवानगी नाही."},
    "Local document file no longer exists.": {
        "hi": "स्थानीय दस्तावेज़ फ़ाइल अब मौजूद नहीं है।",
        "mr": "स्थानिक दस्तऐवज फाईल आता अस्तित्वात नाही."},
    "Please analyze this document first.": {
        "hi": "कृपया पहले इस दस्तावेज़ का विश्लेषण करें।",
        "mr": "कृपया आधी या दस्तऐवजाचे विश्लेषण करा."},
    "Could not read the document. Please try again.": {
        "hi": "दस्तावेज़ पढ़ा नहीं जा सका। कृपया पुनः प्रयास करें।",
        "mr": "दस्तऐवज वाचता आला नाही. कृपया पुन्हा प्रयत्न करा."},
    "Could not retrieve the document file from remote storage.": {
        "hi": "रिमोट स्टोरेज से दस्तावेज़ फ़ाइल प्राप्त नहीं की जा सकी।",
        "mr": "रिमोट स्टोरेजमधून दस्तऐवज फाईल मिळवता आली नाही."},
    "The original document file is no longer available on temporary server storage. Please re-upload the document to run a new analysis.": {
        "hi": "मूल दस्तावेज़ फ़ाइल अस्थायी सर्वर स्टोरेज पर अब उपलब्ध नहीं है। नया विश्लेषण चलाने के लिए कृपया दस्तावेज़ दोबारा अपलोड करें।",
        "mr": "मूळ दस्तऐवज फाईल तात्पुरत्या सर्व्हर स्टोरेजवर आता उपलब्ध नाही. नवीन विश्लेषणासाठी कृपया दस्तऐवज पुन्हा अपलोड करा."},
    "Too many concurrent analysis requests. Please wait for your pending document analysis to finish.": {
        "hi": "एक साथ बहुत सारे विश्लेषण अनुरोध हैं। कृपया अपने लंबित दस्तावेज़ विश्लेषण के पूरा होने की प्रतीक्षा करें।",
        "mr": "एकाच वेळी खूप विश्लेषण विनंत्या आहेत. कृपया तुमचे प्रलंबित दस्तऐवज विश्लेषण पूर्ण होईपर्यंत थांबा."},
    "Could not translate the analysis right now. Please try again.": {
        "hi": "विश्लेषण का अनुवाद अभी नहीं हो सका। कृपया पुनः प्रयास करें।",
        "mr": "विश्लेषणाचे भाषांतर आत्ता करता आले नाही. कृपया पुन्हा प्रयत्न करा."},
    # ── analysis job errors ───────────────────────────────────────────────────
    "Analysis failed. Please try again.": {
        "hi": "विश्लेषण विफल रहा। कृपया पुनः प्रयास करें।",
        "mr": "विश्लेषण अयशस्वी झाले. कृपया पुन्हा प्रयत्न करा."},
    "The AI service is busy right now. Please try again in a minute.": {
        "hi": "AI सेवा अभी व्यस्त है। कृपया एक मिनट बाद पुनः प्रयास करें।",
        "mr": "AI सेवा सध्या व्यस्त आहे. कृपया एका मिनिटाने पुन्हा प्रयत्न करा."},
    "Analysis timed out. The document may be too large — please try again.": {
        "hi": "विश्लेषण का समय समाप्त हो गया। दस्तावेज़ बहुत बड़ा हो सकता है — कृपया पुनः प्रयास करें।",
        "mr": "विश्लेषणाची वेळ संपली. दस्तऐवज खूप मोठा असू शकतो — कृपया पुन्हा प्रयत्न करा."},
    "Analysis did not finish (the server may have restarted). Please re-analyze.": {
        "hi": "विश्लेषण पूरा नहीं हुआ (सर्वर पुनः आरंभ हुआ हो सकता है)। कृपया दोबारा विश्लेषण करें।",
        "mr": "विश्लेषण पूर्ण झाले नाही (सर्व्हर पुन्हा सुरू झाला असावा). कृपया पुन्हा विश्लेषण करा."},
    "No sufficiently readable text could be extracted from this document. If it is scanned, enable OCR; otherwise upload a valid text-based PDF or a clearer image.": {
        "hi": "इस दस्तावेज़ से पर्याप्त पढ़ने योग्य टेक्स्ट नहीं निकाला जा सका। यदि यह स्कैन किया हुआ है तो OCR चालू करें; अन्यथा मान्य टेक्स्ट-आधारित PDF या अधिक स्पष्ट छवि अपलोड करें।",
        "mr": "या दस्तऐवजातून पुरेसा वाचता येणारा मजकूर काढता आला नाही. तो स्कॅन केलेला असल्यास OCR सुरू करा; अन्यथा वैध टेक्स्ट-आधारित PDF किंवा अधिक स्पष्ट प्रतिमा अपलोड करा."},
    "The document was split for processing, but too little readable text was extracted. For scanned PDFs, enable OCR or upload a clearer/searchable PDF.": {
        "hi": "प्रोसेसिंग के लिए दस्तावेज़ को विभाजित किया गया, लेकिन बहुत कम पढ़ने योग्य टेक्स्ट निकला। स्कैन किए गए PDF के लिए OCR चालू करें या अधिक स्पष्ट/खोज-योग्य PDF अपलोड करें।",
        "mr": "प्रक्रियेसाठी दस्तऐवज विभागला गेला, पण खूप कमी वाचता येणारा मजकूर मिळाला. स्कॅन केलेल्या PDF साठी OCR सुरू करा किंवा अधिक स्पष्ट/शोधण्यायोग्य PDF अपलोड करा."},
    "Unknown error": {"hi": "अज्ञात त्रुटि।", "mr": "अज्ञात त्रुटी."},
    # ── AI endpoints ──────────────────────────────────────────────────────────
    "The AI could not answer right now. Please try again.": {
        "hi": "AI अभी उत्तर नहीं दे सका। कृपया पुनः प्रयास करें।",
        "mr": "AI ला आत्ता उत्तर देता आले नाही. कृपया पुन्हा प्रयत्न करा."},
    "Provide at least one document ID.": {
        "hi": "कृपया कम से कम एक दस्तावेज़ आईडी दें।",
        "mr": "कृपया किमान एक दस्तऐवज आयडी द्या."},
    "No readable documents found for multi-document Q&A.": {
        "hi": "बहु-दस्तावेज़ प्रश्नोत्तर के लिए कोई पठनीय दस्तावेज़ नहीं मिला।",
        "mr": "बहु-दस्तऐवज प्रश्नोत्तरासाठी वाचता येणारा कोणताही दस्तऐवज सापडला नाही."},
    "Please describe your legal question.": {
        "hi": "कृपया अपना कानूनी प्रश्न बताएँ।",
        "mr": "कृपया तुमचा कायदेशीर प्रश्न सांगा."},
    "The advisor could not answer right now. Please try again.": {
        "hi": "सलाहकार अभी उत्तर नहीं दे सका। कृपया पुनः प्रयास करें।",
        "mr": "सल्लागाराला आत्ता उत्तर देता आले नाही. कृपया पुन्हा प्रयत्न करा."},
    "Could not generate consequences right now. Please try again.": {
        "hi": "परिणाम अभी तैयार नहीं हो सके। कृपया पुनः प्रयास करें।",
        "mr": "परिणाम आत्ता तयार करता आले नाहीत. कृपया पुन्हा प्रयत्न करा."},
    "Could not generate negotiation guidance right now. Please try again.": {
        "hi": "बातचीत संबंधी मार्गदर्शन अभी तैयार नहीं हो सका। कृपया पुनः प्रयास करें।",
        "mr": "वाटाघाटीबाबत मार्गदर्शन आत्ता तयार करता आले नाही. कृपया पुन्हा प्रयत्न करा."},
    # ── auth ──────────────────────────────────────────────────────────────────
    "Invalid token": {"hi": "अमान्य टोकन।", "mr": "अवैध टोकन."},
    "User not found": {"hi": "उपयोगकर्ता नहीं मिला।", "mr": "वापरकर्ता सापडला नाही."},
    "Session expired. Please sign in again.": {
        "hi": "सत्र समाप्त हो गया। कृपया फिर से साइन इन करें।",
        "mr": "सत्र संपले. कृपया पुन्हा साइन इन करा."},
    "Authentication required": {"hi": "प्रमाणीकरण आवश्यक है।", "mr": "प्रमाणीकरण आवश्यक आहे."},
    "Administrator access required.": {
        "hi": "व्यवस्थापक (एडमिन) अनुमति आवश्यक है।",
        "mr": "प्रशासक (अॅडमिन) परवानगी आवश्यक आहे."},
    "Email already registered": {"hi": "यह ईमेल पहले से पंजीकृत है।", "mr": "हा ईमेल आधीच नोंदणीकृत आहे."},
    "Invalid email or password": {"hi": "ईमेल या पासवर्ड गलत है।", "mr": "ईमेल किंवा पासवर्ड चुकीचा आहे."},
    "This reset link is invalid or has already been used.": {
        "hi": "यह रीसेट लिंक अमान्य है या पहले ही उपयोग हो चुका है।",
        "mr": "ही रीसेट लिंक अवैध आहे किंवा आधीच वापरली गेली आहे."},
    "This reset link has expired. Please request a new one.": {
        "hi": "यह रीसेट लिंक समाप्त हो चुका है। कृपया नया अनुरोध करें।",
        "mr": "ही रीसेट लिंक कालबाह्य झाली आहे. कृपया नवीन विनंती करा."},
    "Password must be at least 8 characters.": {
        "hi": "पासवर्ड कम से कम 8 अक्षरों का होना चाहिए।",
        "mr": "पासवर्ड किमान 8 अक्षरांचा असावा."},
    "Password must be at most 72 bytes (bcrypt limit).": {
        "hi": "पासवर्ड अधिकतम 72 बाइट का हो सकता है (bcrypt सीमा)।",
        "mr": "पासवर्ड जास्तीत जास्त 72 बाइटचा असू शकतो (bcrypt मर्यादा)."},
    "Name is required (max 120 characters).": {
        "hi": "नाम आवश्यक है (अधिकतम 120 अक्षर)।",
        "mr": "नाव आवश्यक आहे (कमाल 120 अक्षरे)."},
    "Google OAuth not configured. Contact support.": {
        "hi": "Google OAuth कॉन्फ़िगर नहीं है। कृपया सहायता से संपर्क करें।",
        "mr": "Google OAuth कॉन्फिगर केलेले नाही. कृपया सपोर्टशी संपर्क साधा."},
    "Invalid Google token": {"hi": "अमान्य Google टोकन।", "mr": "अवैध Google टोकन."},
    "Failed to verify token with Google": {
        "hi": "Google के साथ टोकन सत्यापित नहीं हो सका।",
        "mr": "Google सोबत टोकन पडताळता आले नाही."},
    "Google token was not issued for this client": {
        "hi": "यह Google टोकन इस क्लाइंट के लिए जारी नहीं किया गया था।",
        "mr": "हे Google टोकन या क्लायंटसाठी जारी केलेले नव्हते."},
    "Invalid token issuer": {"hi": "टोकन जारीकर्ता अमान्य है।", "mr": "टोकन जारीकर्ता अवैध आहे."},
    "Your Google email address is not verified.": {
        "hi": "आपका Google ईमेल पता सत्यापित नहीं है।",
        "mr": "तुमचा Google ईमेल पत्ता पडताळलेला नाही."},
    "Google account has no email address": {
        "hi": "Google खाते में ईमेल पता नहीं है।",
        "mr": "Google खात्यात ईमेल पत्ता नाही."},
    # ── upload ────────────────────────────────────────────────────────────────
    "Uploaded file is empty.": {"hi": "अपलोड की गई फ़ाइल खाली है।", "mr": "अपलोड केलेली फाईल रिकामी आहे."},
    "Unsupported file type. Please upload a PDF or an image (JPG, PNG, or WebP) of the document. Make sure the file is valid and not corrupted or renamed.": {
        "hi": "असमर्थित फ़ाइल प्रकार। कृपया दस्तावेज़ का PDF या छवि (JPG, PNG या WebP) अपलोड करें। सुनिश्चित करें कि फ़ाइल मान्य है और खराब या नाम बदली हुई नहीं है।",
        "mr": "असमर्थित फाईल प्रकार. कृपया दस्तऐवजाचा PDF किंवा प्रतिमा (JPG, PNG किंवा WebP) अपलोड करा. फाईल वैध असून खराब किंवा नाव बदललेली नाही याची खात्री करा."},
    "Corrupted or invalid PDF document file.": {
        "hi": "PDF फ़ाइल खराब या अमान्य है।",
        "mr": "PDF फाईल खराब किंवा अवैध आहे."},
    "File storage is temporarily unavailable. Please try again.": {
        "hi": "फ़ाइल स्टोरेज अस्थायी रूप से उपलब्ध नहीं है। कृपया पुनः प्रयास करें।",
        "mr": "फाईल स्टोरेज तात्पुरते उपलब्ध नाही. कृपया पुन्हा प्रयत्न करा."},
    "Durable file storage is not configured on the server.": {
        "hi": "सर्वर पर स्थायी फ़ाइल स्टोरेज कॉन्फ़िगर नहीं है।",
        "mr": "सर्व्हरवर कायमस्वरूपी फाईल स्टोरेज कॉन्फिगर केलेले नाही."},
    "Sign in to view document history.": {
        "hi": "दस्तावेज़ इतिहास देखने के लिए साइन इन करें।",
        "mr": "दस्तऐवज इतिहास पाहण्यासाठी साइन इन करा."},
    # ── hubs / applications / checklist ──────────────────────────────────────
    "Invalid status value": {"hi": "स्थिति का मान अमान्य है।", "mr": "स्थितीचे मूल्य अवैध आहे."},
    "Application not found or unauthorized.": {
        "hi": "आवेदन नहीं मिला या आपको अनुमति नहीं है।",
        "mr": "अर्ज सापडला नाही किंवा तुम्हाला परवानगी नाही."},
    "Checklist item not found.": {
        "hi": "चेकलिस्ट आइटम नहीं मिला।",
        "mr": "चेकलिस्ट आयटम सापडला नाही."},
    # ── yojana / share / shadow ──────────────────────────────────────────────
    "Government scheme not found.": {
        "hi": "सरकारी योजना नहीं मिली।",
        "mr": "सरकारी योजना सापडली नाही."},
    "Notice text is too short to parse.": {
        "hi": "सूचना का पाठ इतना छोटा है कि उसे पढ़ा नहीं जा सकता।",
        "mr": "सूचनेचा मजकूर विश्लेषणासाठी खूपच लहान आहे."},
    "AI Citizen Guide not found.": {
        "hi": "AI नागरिक मार्गदर्शिका नहीं मिली।",
        "mr": "AI नागरिक मार्गदर्शिका सापडली नाही."},
    "Share link is invalid, expired, or revoked.": {
        "hi": "शेयर लिंक अमान्य, समाप्त या रद्द है।",
        "mr": "शेअर लिंक अवैध, कालबाह्य किंवा रद्द केलेली आहे."},
    "Unable to revoke share link.": {
        "hi": "शेयर लिंक रद्द नहीं की जा सकी।",
        "mr": "शेअर लिंक रद्द करता आली नाही."},
    "Comparison record not found.": {
        "hi": "तुलना रिकॉर्ड नहीं मिला।",
        "mr": "तुलना नोंद सापडली नाही."},
    "Forbidden: Invalid or missing X-Shadow-Admin-Key header.": {
        "hi": "निषिद्ध: X-Shadow-Admin-Key हेडर अमान्य है या मौजूद नहीं है।",
        "mr": "प्रतिबंधित: X-Shadow-Admin-Key हेडर अवैध आहे किंवा नाही."},
    # ── framework defaults ───────────────────────────────────────────────────
    "Cross-origin request blocked.": {
        "hi": "क्रॉस-ओरिजिन अनुरोध अवरुद्ध किया गया।",
        "mr": "क्रॉस-ओरिजिन विनंती अवरोधित केली."},
    "Document file is not available.": {
        "hi": "दस्तावेज़ फ़ाइल उपलब्ध नहीं है।",
        "mr": "दस्तऐवज फाईल उपलब्ध नाही."},
    "File storage is temporarily unavailable.": {
        "hi": "फ़ाइल स्टोरेज अस्थायी रूप से उपलब्ध नहीं है।",
        "mr": "फाईल स्टोरेज तात्पुरते उपलब्ध नाही."},
    "Requires registered agricultural landholding": {
        "hi": "पंजीकृत कृषि भूमि-धारण आवश्यक है",
        "mr": "नोंदणीकृत शेतजमीन धारणा आवश्यक आहे"},
    "No audio file was received.": {
        "hi": "कोई ऑडियो फ़ाइल प्राप्त नहीं हुई।",
        "mr": "कोणतीही ऑडिओ फाईल मिळाली नाही."},
    "Audio is too large. Maximum allowed size is 10 MB.": {
        "hi": "ऑडियो बहुत बड़ा है। अधिकतम अनुमत आकार 10 MB है।",
        "mr": "ऑडिओ खूप मोठा आहे. कमाल परवानगी असलेला आकार 10 MB आहे."},
    "Audio is too long. Please keep it under 60 seconds.": {
        "hi": "ऑडियो बहुत लंबा है। कृपया इसे 60 सेकंड से कम रखें।",
        "mr": "ऑडिओ खूप लांब आहे. कृपया तो 60 सेकंदांपेक्षा कमी ठेवा."},
    "Unsupported audio format. Please use webm, ogg, mp4, m4a, wav or mp3.": {
        "hi": "असमर्थित ऑडियो प्रारूप। कृपया webm, ogg, mp4, m4a, wav या mp3 का उपयोग करें।",
        "mr": "असमर्थित ऑडिओ स्वरूप. कृपया webm, ogg, mp4, m4a, wav किंवा mp3 वापरा."},
    "The audio is empty or too short. Please record again.": {
        "hi": "ऑडियो खाली या बहुत छोटा है। कृपया फिर से रिकॉर्ड करें।",
        "mr": "ऑडिओ रिकामा किंवा खूप लहान आहे. कृपया पुन्हा रेकॉर्ड करा."},
    "We could not hear anything clear. Please speak again.": {
        "hi": "कुछ स्पष्ट सुनाई नहीं दिया। कृपया फिर से बोलें।",
        "mr": "काही स्पष्ट ऐकू आले नाही. कृपया पुन्हा बोला."},
    "Speech recognition is busy. Please try again in a moment.": {
        "hi": "स्पीच रिकग्निशन व्यस्त है। कृपया थोड़ी देर बाद पुनः प्रयास करें।",
        "mr": "स्पीच रेकग्निशन व्यस्त आहे. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा."},
    "Speech recognition is temporarily unavailable. Please try again later.": {
        "hi": "स्पीच रिकग्निशन अस्थायी रूप से उपलब्ध नहीं है। कृपया बाद में पुनः प्रयास करें।",
        "mr": "स्पीच रेकग्निशन तात्पुरते उपलब्ध नाही. कृपया नंतर पुन्हा प्रयत्न करा."},
    "Not Found": {"hi": "अनुरोधित संसाधन नहीं मिला।", "mr": "विनंती केलेले संसाधन सापडले नाही."},
    "Method Not Allowed": {"hi": "यह अनुरोध विधि अनुमत नहीं है।", "mr": "ही विनंती पद्धत अनुमत नाही."},
    "Not authenticated": {"hi": "प्रमाणीकरण आवश्यक है।", "mr": "प्रमाणीकरण आवश्यक आहे."},
    "Internal Server Error": {"hi": "सर्वर में आंतरिक त्रुटि हुई।", "mr": "सर्व्हरमध्ये अंतर्गत त्रुटी आली."},
    "Too many requests. Please slow down and try again shortly.": {
        "hi": "बहुत अधिक अनुरोध। कृपया धीमे करें और थोड़ी देर बाद पुनः प्रयास करें।",
        "mr": "खूप विनंत्या. कृपया थोडे थांबा आणि थोड्या वेळाने पुन्हा प्रयत्न करा."},
}

# Dynamic messages: (compiled regex, {lang: template using \1 group refs via str.format with named groups})
PATTERNS: list[tuple[re.Pattern, dict[str, str]]] = [
    (re.compile(r"^File too large\. Maximum allowed size is (?P<n>[\d.]+) MB\.$"), {
        "hi": "फ़ाइल बहुत बड़ी है। अधिकतम अनुमत आकार {n} MB है।",
        "mr": "फाईल खूप मोठी आहे. कमाल परवानगी असलेला आकार {n} MB आहे."}),
    (re.compile(r"^Document exceeds the maximum limit of (?P<n>\d+) pages\. Please upload a shorter document or excerpt\.$"), {
        "hi": "दस्तावेज़ अधिकतम {n} पृष्ठों की सीमा से अधिक है। कृपया छोटा दस्तावेज़ या अंश अपलोड करें।",
        "mr": "दस्तऐवज कमाल {n} पानांच्या मर्यादेपेक्षा जास्त आहे. कृपया लहान दस्तऐवज किंवा उतारा अपलोड करा."}),
    (re.compile(r"^File extension '(?P<ext>[^']*)' does not match the actual file content \(detected: (?P<mime>[^)]*)\)\. Please upload the correct file\.$"), {
        "hi": "फ़ाइल एक्सटेंशन '{ext}' वास्तविक फ़ाइल सामग्री ({mime}) से मेल नहीं खाता। कृपया सही फ़ाइल अपलोड करें।",
        "mr": "फाईल एक्स्टेंशन '{ext}' प्रत्यक्ष फाईल मजकुराशी ({mime}) जुळत नाही. कृपया योग्य फाईल अपलोड करा."}),
    (re.compile(r"^Invalid (?P<kind>business|property|ID) type: (?P<v>.*)$"), {
        "hi": "अमान्य प्रकार: {v}",
        "mr": "अवैध प्रकार: {v}"}),
    (re.compile(r"^Service '(?P<s>[^']*)' not found for (?P<kind>business|property|ID) type '(?P<t>[^']*)'$"), {
        "hi": "'{t}' प्रकार के लिए सेवा '{s}' नहीं मिली।",
        "mr": "'{t}' प्रकारासाठी सेवा '{s}' सापडली नाही."}),
    (re.compile(r"^(?:Business|Property|ID) type '(?P<t>[^']*)' not found$"), {
        "hi": "प्रकार '{t}' नहीं मिला।",
        "mr": "प्रकार '{t}' सापडला नाही."}),
    (re.compile(r"^Unsupported service domain '(?P<d>[^']*)'$"), {
        "hi": "असमर्थित सेवा क्षेत्र '{d}'।",
        "mr": "असमर्थित सेवा क्षेत्र '{d}'."}),
    (re.compile(r"^Family annual income exceeds scheme limit of (?P<n>.+)$"), {
        "hi": "परिवार की वार्षिक आय योजना की सीमा {n} से अधिक है",
        "mr": "कुटुंबाचे वार्षिक उत्पन्न योजनेच्या {n} मर्यादेपेक्षा जास्त आहे"}),
    (re.compile(r"^Age requirement is between (?P<a>\d+) and (?P<b>\d+) years \(Your age: (?P<c>\d+)\)$"), {
        "hi": "आयु की आवश्यकता {a} से {b} वर्ष के बीच है (आपकी आयु: {c})",
        "mr": "वयाची अट {a} ते {b} वर्षांदरम्यान आहे (तुमचे वय: {c})"}),
    (re.compile(r"^Scheme is exclusively for (?P<g>Male|Female) beneficiaries$"), {
        "hi": "यह योजना केवल लाभार्थी ({g}) के लिए है",
        "mr": "ही योजना केवळ लाभार्थी ({g}) साठी आहे"}),
    (re.compile(r"^Targeted primarily for: (?P<o>.*)$"), {
        "hi": "मुख्य रूप से इनके लिए: {o}",
        "mr": "प्रामुख्याने यांच्यासाठी: {o}"}),
    (re.compile(r"^Applicable only for residents of: (?P<o>.*)$"), {
        "hi": "केवल इन राज्यों के निवासियों के लिए: {o}",
        "mr": "फक्त या राज्यांतील रहिवाशांसाठी: {o}"}),
    (re.compile(r"^Landholding exceeds maximum limit of (?P<n>.+) acres$"), {
        "hi": "भूमि-धारण {n} एकड़ की अधिकतम सीमा से अधिक है",
        "mr": "जमीनधारणा कमाल {n} एकर मर्यादेपेक्षा जास्त आहे"}),
    (re.compile(r"^Rate limit exceeded: (?P<r>.*)$"), {
        "hi": "अनुरोध सीमा पार हो गई: {r}। कृपया थोड़ी देर बाद पुनः प्रयास करें।",
        "mr": "विनंती मर्यादा ओलांडली: {r}. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा."}),
]


def translate_message(text, lang: Optional[str]):
    """Translate a catalog message into ``lang``; unknown strings / non-strings pass through unchanged."""
    lang = normalize_lang(lang)
    if lang == "en" or not isinstance(text, str):
        return text
    entry = MESSAGES.get(text) or MESSAGES.get(text.strip())
    if entry and lang in entry:
        return entry[lang]
    for pattern, templates in PATTERNS:
        m = pattern.match(text.strip())
        if m and lang in templates:
            return templates[lang].format(**m.groupdict())
    return text
