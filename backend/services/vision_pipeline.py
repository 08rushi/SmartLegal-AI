"""
vision_pipeline.py — Visual / OCR Processing Pipeline (Phase 4).

Implements the multi-stage visual transcription cascade for scanned and image documents:

    Scanned / Image Page
            │
            ▼
      Gemini Vision
            │
       success?
       /       \
     YES        NO
      │          │
      ▼          ▼
 PageTranscription   PaddleOCR
                         │
                    acceptable?
                     /       \
                   YES        NO
                    │          │
                    ▼          ▼
                transcription  Tesseract
                               │
                               ▼
                           transcription

Key Architectural Rules:
  1. Digital Page Bypass: Clean digital pages (page_type == 'digital') bypass the visual
     pipeline completely and retain native PyMuPDF extractions.
  2. Gemini Vision Primary: Config-driven via ModelCapability (gemini-3.8-flash, etc.).
     Strictly forbids obsolete/retired model IDs (gemini-1.5, gemini-2.0, gemini-2.5).
  3. Transcription Only: Prompts enforce strict verbatim transcription with script preservation,
     structure retention, and zero legal interpretation/conclusion generation.
  4. Uncertainty Markers: Genuine [UNCLEAR] tokens preserved for indecipherable text.
  5. Privacy Mode: If privacy_mode is active or cloud_vision is disabled, Gemini Vision
     is skipped and routing directs immediately to permitted local OCR engines.
  6. Quality-Aware Fallback: Deterministic quality gating for PaddleOCR before deciding
     whether to accept the result or fall back to Tesseract.
  7. Full Provenance & Auditability: Retains extraction_source ('pymupdf', 'gemini_vision',
     'paddleocr', 'tesseract') and structured fallback_history on every page.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import fitz  # PyMuPDF
from PIL import Image

from config import get_settings
from services.model_capabilities import get_capability, get_gemini_vision_model, ModelCapability
from services.ocr_service import _lang_string, _resolve
from services.page_content import (
    PageContent,
    calculate_digital_quality,
    calculate_ocr_quality,
    _is_letter,
)
from services.page_transcription import PageTranscription
from services.pdf_parser import detect_script

logger = logging.getLogger(__name__)


# =============================================================================
# Prompts & Constants
# =============================================================================

TRANSCRIPTION_SYSTEM_PROMPT = """You are an expert legal document transcription system.
Your task is to transcribe verbatim the exact textual content present on this document page.

MANDATORY RULES:
1. PRESERVE ORIGINAL TEXT & SCRIPT: Transcribe all text exactly as written in its original language and script (e.g. Hindi/Devanagari, Tamil, Telugu, Bengali, Gujarati, Marathi, English). DO NOT TRANSLATE.
2. PRESERVE STRUCTURE: Retain headings, numbered clauses (e.g. 1.1, Clause 5), bullet points, and tables where reasonably representable.
3. DO NOT SUMMARIZE OR REWRITE: Output the literal text without commentary, additions, or paraphrasing.
4. DO NOT INVENT TEXT: If text is torn, cut off, obscured, or illegible, do not guess or extrapolate.
5. MARK UNREADABLE PORTIONS: Mark any genuinely unreadable, blurred, or illegible words as [UNCLEAR].
6. NO LEGAL OPINIONS: Do NOT analyze legal risk, provide legal advice, or draw legal conclusions. Only transcribe the visual document.
7. HANDWRITING: Pages may be partly or fully handwritten (including Indian-language handwriting, stamps, signatures and filled-in forms). Read carefully, use surrounding context to resolve ambiguous letters or digits (names, amounts, dates), but never invent text — mark genuinely illegible words as [UNCLEAR]. Note signatures/stamps as [SIGNATURE] / [STAMP].

Output ONLY the transcribed document text."""

BATCH_INSTRUCTIONS = """You will receive {n} document page images, each preceded by a marker line "=== PAGE <number> ===".
Transcribe EVERY page following the rules below. Begin each page's transcription with exactly the same marker line
("=== PAGE <number> ===") on its own line, in the same order, and output nothing before the first marker.
If a page is blank, output only its marker line.

"""

_PAGE_MARKER_RE = re.compile(r"(?m)^\s*=+\s*PAGE\s+(\d+)\s*=+\s*$")


def split_batch_pages(raw_text: str, expected_pages: List[int]) -> Dict[int, str]:
    """Split a multi-page transcription on '=== PAGE n ===' markers into {page_num: text}."""
    expected = set(expected_pages)
    pieces = _PAGE_MARKER_RE.split(raw_text or "")
    out: Dict[int, str] = {}
    if len(pieces) == 1:
        # No markers at all: only trustworthy when exactly one page was requested.
        if len(expected_pages) == 1 and pieces[0].strip():
            out[expected_pages[0]] = pieces[0].strip()
        return out
    # pieces = [preamble, num1, text1, num2, text2, ...]
    for i in range(1, len(pieces) - 1, 2):
        num = int(pieces[i])
        if num in expected and num not in out:
            out[num] = pieces[i + 1].strip()
    return out


# =============================================================================
# Error Classification
# =============================================================================

def classify_vision_error(exc: Exception) -> str:
    """
    Deterministically categorize vision/OCR errors:
      - 'provider_unavailable': Missing API key, model unconfigured, or service disabled
      - 'rate_limit': HTTP 429, quota exceeded, TPM/RPM limits
      - 'timeout': Connection timed out, ReadTimeout
      - 'auth_failure': HTTP 401, 403, invalid credentials
      - 'invalid_image': Corrupt image payload, unreadable format
      - 'malformed_response': Empty response payload or JSON decode errors
    """
    msg = str(exc).lower()

    if "401" in msg or "403" in msg or "permission" in msg or "unauthorized" in msg or "api_key" in msg:
        return "auth_failure"
    if "429" in msg or "rate_limit" in msg or "quota" in msg or "resourceexhausted" in msg:
        return "rate_limit"
    if "timeout" in msg or "timed out" in msg or "deadline" in msg:
        return "timeout"
    if "image" in msg and ("corrupt" in msg or "unidentified" in msg or "cannot identify" in msg or "invalid" in msg):
        return "invalid_image"
    if "empty" in msg or "malformed" in msg or "decode" in msg or "no candidate" in msg:
        return "malformed_response"
    if "not configured" in msg or "disabled" in msg or "not installed" in msg:
        return "provider_unavailable"

    return "provider_unavailable"


# =============================================================================
# Quality Evaluation Helper
# =============================================================================

def evaluate_transcription_quality(
    text: str,
    confidence: Optional[float] = None,
) -> Tuple[float, bool, bool, Dict[str, Any]]:
    """
    Deterministically evaluate transcription quality against measurable signals.

    Returns:
      (quality_score, is_unclear, is_acceptable, signals)

    Criteria for is_acceptable:
      1. text must be non-empty (stripped).
      2. alpha_count >= DIGITAL_MIN_LETTERS (or >= 15 for concise single-clause pages).
      3. letter_ratio >= DIGITAL_MIN_LETTER_RATIO (0.40) to weed out noisy raster artifacts.
      4. If genuine confidence is provided, it must be >= OCR_MIN_CONFIDENCE_THRESHOLD (0.35).
    """
    settings = get_settings()
    clean_text = text.strip()

    if not clean_text:
        return 0.0, True, False, {
            "char_count": 0,
            "word_count": 0,
            "alpha_count": 0,
            "letter_ratio": 0.0,
            "has_unclear": False,
        }

    alpha_count = sum(1 for ch in clean_text if _is_letter(ch))
    non_space_count = sum(1 for ch in clean_text if not ch.isspace())
    letter_ratio = (alpha_count / float(non_space_count)) if non_space_count > 0 else 0.0
    has_unclear = "[UNCLEAR]" in clean_text

    signals = {
        "char_count": len(clean_text),
        "word_count": len(clean_text.split()),
        "alpha_count": alpha_count,
        "letter_ratio": round(letter_ratio, 4),
        "has_unclear": has_unclear,
        "reported_confidence": confidence,
    }

    # Use Phase 2 deterministic calculation: OCR quality if confidence is available,
    # otherwise typographic digital quality
    if confidence is not None:
        quality_score, base_is_unclear, _ = calculate_ocr_quality(confidence, clean_text)
    else:
        quality_score, base_is_unclear, _ = calculate_digital_quality(clean_text)

    is_unclear = base_is_unclear or has_unclear

    # Acceptable gating
    min_letters = min(settings.digital_min_letters, 15)
    is_acceptable = (
        alpha_count >= min_letters
        and letter_ratio >= settings.digital_min_letter_ratio
        and (confidence is None or confidence >= settings.ocr_min_confidence_threshold)
    )

    return quality_score, is_unclear, is_acceptable, signals


# =============================================================================
# 1. Gemini Vision Adapter (Primary Visual Path)
# =============================================================================

class GeminiVisionAdapter:
    """
    Primary Cloud Visual AI Adapter using Google Gemini.

    Configuration-driven:
      - Reads GEMINI_VISION_MODEL via ModelCapability registry (validates non-retired 3.x model).
      - Rejects retired Gemini 1.5, 2.0, and 2.5 series models.
      - Uses modern google.genai SDK if installed; falls back to direct async HTTPX REST calls.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._capability: Optional[ModelCapability] = None

    def get_model_capability(self) -> ModelCapability:
        """Resolve and validate the configured Gemini vision model capability."""
        if self._capability is None:
            self._capability = get_gemini_vision_model()
        return self._capability

    def is_available(self) -> Tuple[bool, str]:
        """Check if Gemini Vision is configured and permitted."""
        if self.settings.privacy_mode:
            return False, "Privacy mode is enabled (cloud visual processing disabled)."
        if not self.settings.cloud_vision_enabled:
            return False, "Cloud vision is disabled by configuration (CLOUD_VISION_ENABLED=False)."
        if not self.settings.gemini_api_key.strip():
            return False, "GEMINI_API_KEY is not configured."

        try:
            cap = self.get_model_capability()
            if not cap.vision_support:
                return False, f"Configured Gemini model {cap.name} does not support vision."
            return True, "ok"
        except Exception as exc:
            return False, str(exc)

    async def transcribe_image(
        self,
        image_bytes: bytes,
        page_num: int = 1,
        mime_type: str = "image/png",
    ) -> PageTranscription:
        """
        Transcribe a single page image using Gemini Vision.
        """
        available, reason = self.is_available()
        if not available:
            raise RuntimeError(f"Gemini Vision unavailable: {reason}")

        cap = self.get_model_capability()
        model_name = cap.name
        api_key = self.settings.gemini_api_key.strip()

        # Validate image payload
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.verify()
        except Exception as exc:
            raise ValueError(f"Corrupted or invalid image payload: {exc}") from exc

        b64_data = base64.b64encode(image_bytes).decode("utf-8")

        # Call Gemini API with timeout and bounded single retry on 429
        last_exc: Optional[Exception] = None
        for attempt in range(2):
            try:
                raw_text, telemetry = await self._call_gemini_api(
                    model_name=model_name,
                    api_key=api_key,
                    b64_data=b64_data,
                    mime_type=mime_type,
                )
                break
            except Exception as exc:
                last_exc = exc
                err_type = classify_vision_error(exc)
                if err_type == "rate_limit" and attempt == 0:
                    logger.warning("[gemini_vision] Rate limited on attempt 1, waiting 1.0s before retry...")
                    await asyncio.sleep(1.0)
                    continue
                raise exc
        else:
            raise last_exc or RuntimeError("Gemini Vision calls exhausted.")

        # Post-process transcription
        script = detect_script(raw_text)
        quality_score, is_unclear, is_acceptable, signals = evaluate_transcription_quality(
            raw_text, confidence=None
        )
        signals.update(telemetry)

        status = "success_with_uncertainty" if is_unclear else "success"
        warnings = []
        if "[UNCLEAR]" in raw_text:
            warnings.append("Document contains genuinely unreadable regions marked as [UNCLEAR].")

        return PageTranscription(
            page_num=page_num,
            text=raw_text,
            extraction_source="gemini_vision",
            engine=model_name,
            script=script,
            confidence=telemetry.get("gemini_confidence"),
            is_unclear=is_unclear,
            quality_score=quality_score,
            status=status,
            has_images=True,
            image_count=1,
            raw_signals=signals,
            warnings=warnings,
        )

    async def transcribe_images_batch(
        self,
        pages: List[Tuple[int, bytes]],
        mime_type: str = "image/jpeg",
    ) -> Dict[int, PageTranscription]:
        """
        Transcribe several page images in ONE Gemini request (4-8x fewer calls than page-by-page).
        Returns {page_num: PageTranscription} for the pages the model returned; callers fall back
        to the single-page path for any page that is missing or low quality.
        """
        available, reason = self.is_available()
        if not available:
            raise RuntimeError(f"Gemini Vision unavailable: {reason}")
        if not pages:
            return {}

        cap = self.get_model_capability()
        parts: List[Dict[str, Any]] = [
            {"text": BATCH_INSTRUCTIONS.format(n=len(pages)) + TRANSCRIPTION_SYSTEM_PROMPT}
        ]
        for page_num, img_bytes in pages:
            parts.append({"text": f"=== PAGE {page_num} ==="})
            parts.append({"inline_data": {"mime_type": mime_type, "data": base64.b64encode(img_bytes).decode("utf-8")}})

        raw_text, telemetry = await self._post_parts(cap.name, self.settings.gemini_api_key.strip(), parts)
        texts = split_batch_pages(raw_text, [p for p, _ in pages])

        out: Dict[int, PageTranscription] = {}
        for page_num, text in texts.items():
            quality_score, is_unclear, _acc, signals = evaluate_transcription_quality(text, confidence=None)
            signals.update(telemetry)
            out[page_num] = PageTranscription(
                page_num=page_num,
                text=text,
                extraction_source="gemini_vision",
                engine=cap.name,
                script=detect_script(text),
                confidence=None,
                is_unclear=is_unclear,
                quality_score=quality_score,
                status="success_with_uncertainty" if is_unclear else "success",
                has_images=True,
                image_count=1,
                raw_signals=signals,
                warnings=(["Document contains genuinely unreadable regions marked as [UNCLEAR]."] if "[UNCLEAR]" in text else []),
            )
        return out

    async def _post_parts(
        self,
        model_name: str,
        api_key: str,
        parts: List[Dict[str, Any]],
        timeout: float = 150.0,
    ) -> Tuple[str, Dict[str, Any]]:
        """POST arbitrary content parts to Gemini (used for multi-image requests)."""
        import httpx

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        gen_cfg: Dict[str, Any] = {"temperature": 0.0, "maxOutputTokens": 32768}
        if "2.5-flash" in model_name:
            gen_cfg["thinkingConfig"] = {"thinkingBudget": 0}   # transcription needs no 'thinking'
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                url,
                headers={"x-goog-api-key": api_key},
                json={"contents": [{"parts": parts}], "generationConfig": gen_cfg},
            )
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini API returned HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned no candidates in response.")
        cand = candidates[0]
        text_parts = (cand.get("content") or {}).get("parts") or []
        text = "".join(str(p.get("text", "")) for p in text_parts if isinstance(p, dict)).strip()
        telemetry: Dict[str, Any] = {"finish_reason": cand.get("finishReason", "STOP"), "model_version": model_name}
        usage = data.get("usageMetadata", {})
        if usage:
            telemetry["prompt_token_count"] = usage.get("promptTokenCount")
            telemetry["candidates_token_count"] = usage.get("candidatesTokenCount")
        return text, telemetry

    async def _call_gemini_api(
        self,
        model_name: str,
        api_key: str,
        b64_data: str,
        mime_type: str,
    ) -> Tuple[str, Dict[str, Any]]:
        """Call Google Generative Language REST endpoint."""
        import httpx

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": TRANSCRIPTION_SYSTEM_PROMPT},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64_data,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 8192,
                **({"thinkingConfig": {"thinkingBudget": 0}} if "2.5-flash" in model_name else {}),
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers={"x-goog-api-key": api_key}, json=payload)

        if resp.status_code != 200:
            raise RuntimeError(f"Gemini API returned HTTP {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned no candidates in response.")

        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        if not parts:
            raise RuntimeError("Gemini response candidate contains no text parts.")

        text = parts[0].get("text", "").strip()

        # Telemetry extraction
        telemetry = {
            "finish_reason": candidate.get("finish_reason", "STOP"),
            "model_version": model_name,
        }
        usage = data.get("usageMetadata", {})
        if usage:
            telemetry["prompt_token_count"] = usage.get("promptTokenCount")
            telemetry["candidates_token_count"] = usage.get("candidatesTokenCount")

        return text, telemetry


# =============================================================================
# 2. PaddleOCR Adapter (First Local OCR Fallback)
# =============================================================================

class PaddleOCRAdapter:
    """
    Dedicated PaddleOCR fallback adapter.

    Gracefully detects library presence. If paddleocr is uninstalled, it safely reports
    unavailable so the pipeline immediately advances to Tesseract without crashing.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._ocr_engine = None

    def is_available(self) -> Tuple[bool, str]:
        """Check if PaddleOCR is installed and enabled."""
        if not self.settings.paddleocr_enabled:
            return False, "PaddleOCR is disabled by configuration (PADDLEOCR_ENABLED=False)."

        try:
            import paddleocr  # noqa: F401
            return True, "ok"
        except ImportError as exc:
            return False, f"PaddleOCR is not installed ({exc})."
        except Exception as exc:
            return False, f"PaddleOCR error ({exc})."

    def _get_engine(self):
        if self._ocr_engine is None:
            from paddleocr import PaddleOCR
            self._ocr_engine = PaddleOCR(use_angle_cls=True, lang="en")
        return self._ocr_engine

    async def transcribe_image(
        self,
        image_bytes: bytes,
        page_num: int = 1,
    ) -> PageTranscription:
        """Transcribe an image page using PaddleOCR."""
        available, reason = self.is_available()
        if not available:
            return PageTranscription(
                page_num=page_num,
                text="",
                extraction_source="paddleocr",
                engine="paddleocr-v4",
                status="provider_unavailable",
                is_unclear=True,
                warnings=[reason],
            )

        import numpy as np

        # Open and convert image to numpy RGB
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode != "RGB":
                img = img.convert("RGB")
            img_np = np.array(img)
        except Exception as exc:
            raise ValueError(f"Corrupted image payload for PaddleOCR: {exc}") from exc

        engine = self._get_engine()
        loop = asyncio.get_event_loop()

        # Run OCR in thread pool
        def _sync_ocr():
            return engine.ocr(img_np, cls=True)

        result = await loop.run_in_executor(None, _sync_ocr)

        # Parse PaddleOCR result format: [[ [bbox, (text, conf)], ... ]]
        lines: List[str] = []
        confidences: List[float] = []

        if result and result[0]:
            for item in result[0]:
                if len(item) >= 2 and isinstance(item[1], (tuple, list)):
                    line_text = str(item[1][0]).strip()
                    conf_val = float(item[1][1])
                    if line_text:
                        lines.append(line_text)
                        confidences.append(conf_val)

        text = "\n".join(lines).strip()
        avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else None
        script = detect_script(text)
        quality_score, is_unclear, is_acceptable, signals = evaluate_transcription_quality(
            text, avg_confidence
        )

        status = "success" if is_acceptable else "success_with_uncertainty"
        warnings = []
        if not is_acceptable:
            warnings.append("PaddleOCR output did not satisfy readability quality gate.")

        return PageTranscription(
            page_num=page_num,
            text=text,
            extraction_source="paddleocr",
            engine="paddleocr-v4",
            script=script,
            confidence=avg_confidence,
            is_unclear=is_unclear,
            quality_score=quality_score,
            status=status,
            has_images=True,
            image_count=1,
            raw_signals=signals,
            warnings=warnings,
        )


# =============================================================================
# 3. Tesseract Adapter (Final Local OCR Fallback)
# =============================================================================

class TesseractAdapter:
    """
    Final Local OCR Fallback Adapter using Tesseract via pytesseract.

    Reuses existing ocr_service configuration and language discovery.
    Extracts genuine word-level confidence and respects Indic language tessdata.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_available(self) -> Tuple[bool, str]:
        """Check if Tesseract binary and pytesseract package are available."""
        if not self.settings.ocr_enabled:
            return False, "Tesseract OCR is disabled by configuration (OCR_ENABLED=False)."
        module, reason = _resolve()
        if module is None:
            return False, reason
        return True, "ok"

    async def transcribe_image(
        self,
        image_bytes: bytes,
        page_num: int = 1,
    ) -> PageTranscription:
        """Transcribe an image page using Tesseract."""
        available, reason = self.is_available()
        if not available:
            return PageTranscription(
                page_num=page_num,
                text="",
                extraction_source="tesseract",
                engine="tesseract",
                status="provider_unavailable",
                is_unclear=True,
                warnings=[reason],
            )

        module, _ = _resolve()
        loop = asyncio.get_event_loop()

        def _sync_ocr() -> Tuple[str, Optional[float]]:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode not in ("L", "RGB"):
                img = img.convert("RGB")

            lang = _lang_string()
            ocr_confidence: Optional[float] = None

            # Extract word confidences
            try:
                output_type = getattr(module, "Output", None)
                dict_type = output_type.DICT if output_type else "dict"
                data = module.image_to_data(img, lang=lang, output_type=dict_type)

                raw_texts = data.get("text", [])
                raw_confs = data.get("conf", [])

                valid_confs: list[float] = []
                for w, c in zip(raw_texts, raw_confs):
                    if str(w).strip():
                        try:
                            c_val = float(c)
                            if c_val >= 0.0:
                                valid_confs.append(c_val)
                        except (ValueError, TypeError):
                            continue

                if valid_confs:
                    ocr_confidence = round(sum(valid_confs) / (len(valid_confs) * 100.0), 3)
            except Exception:
                ocr_confidence = None

            text = (module.image_to_string(img, lang=lang) or "").strip()
            return text, ocr_confidence

        text, confidence = await loop.run_in_executor(None, _sync_ocr)
        script = detect_script(text)
        quality_score, is_unclear, is_acceptable, signals = evaluate_transcription_quality(
            text, confidence
        )

        status = "success" if is_acceptable else "success_with_uncertainty"
        warnings = []
        if not is_acceptable:
            warnings.append("Tesseract output has low readability quality.")

        return PageTranscription(
            page_num=page_num,
            text=text,
            extraction_source="tesseract",
            engine="tesseract",
            script=script,
            confidence=confidence,
            is_unclear=is_unclear,
            quality_score=quality_score,
            status=status,
            has_images=True,
            image_count=1,
            raw_signals=signals,
            warnings=warnings,
        )


# =============================================================================
# 4. Visual Document Pipeline Coordinator
# =============================================================================

class VisualDocumentPipeline:
    """
    Main Visual Processing Coordinator.

    Manages:
      - Clean digital page bypass (native PyMuPDF extraction preserved).
      - Gemini Vision primary visual attempt (transcription only, script preservation).
      - PaddleOCR first local fallback with quality gating.
      - Tesseract final local fallback.
      - Page-by-page mixed PDF processing.
      - Standalone image document processing.
      - Auditable attempt history tracking on every page.
    """

    def __init__(
        self,
        gemini_adapter: Optional[GeminiVisionAdapter] = None,
        paddleocr_adapter: Optional[PaddleOCRAdapter] = None,
        tesseract_adapter: Optional[TesseractAdapter] = None,
    ) -> None:
        self.settings = get_settings()
        self.gemini_adapter = gemini_adapter or GeminiVisionAdapter()
        self.paddleocr_adapter = paddleocr_adapter or PaddleOCRAdapter()
        self.tesseract_adapter = tesseract_adapter or TesseractAdapter()

    async def transcribe_page_image(
        self,
        image_bytes: bytes,
        page_num: int = 1,
        existing_page: Optional[PageContent] = None,
    ) -> PageTranscription:
        """
        Execute the quality-aware visual waterfall for a single page image.
        """
        # ── Step 0: Digital Page Bypass ────────────────────────────────────────
        if (
            existing_page is not None
            and existing_page.page_type == "digital"
            and not existing_page.is_unclear
            and existing_page.text.strip()
        ):
            return PageTranscription(
                page_num=page_num,
                text=existing_page.text,
                extraction_source="pymupdf",
                engine="pymupdf",
                script=existing_page.script,
                confidence=None,
                is_unclear=False,
                quality_score=existing_page.quality_score,
                status="success",
                char_count=existing_page.char_count,
                word_count=existing_page.word_count,
                has_images=existing_page.has_images,
                image_count=existing_page.image_count,
                raw_signals=existing_page.raw_signals,
                fallback_history=[],
            )

        fallback_history: List[Dict[str, Any]] = []

        # ── Step 1: Gemini Vision (Primary Visual Path) ─────────────────────────
        can_use_gemini, gemini_reason = self.gemini_adapter.is_available()
        if can_use_gemini:
            try:
                trans = await self.gemini_adapter.transcribe_image(image_bytes, page_num=page_num)
                fallback_history.append({
                    "engine": "gemini_vision",
                    "status": "success",
                    "quality_score": trans.quality_score,
                    "is_unclear": trans.is_unclear,
                })
                # Check acceptance
                _, _, is_acc, _ = evaluate_transcription_quality(trans.text, trans.confidence)
                if is_acc:
                    trans.fallback_history = fallback_history
                    return trans
                else:
                    fallback_history[-1]["status"] = "rejected_low_quality"
            except Exception as exc:
                err_type = classify_vision_error(exc)
                fallback_history.append({
                    "engine": "gemini_vision",
                    "status": "failed",
                    "error_type": err_type,
                    "message": str(exc),
                })
                logger.warning(f"[visual_pipeline] Gemini Vision failed on page {page_num} ({err_type}): {exc}")
        else:
            fallback_history.append({
                "engine": "gemini_vision",
                "status": "skipped",
                "reason": gemini_reason,
            })

        # ── Step 2: PaddleOCR (First Local OCR Fallback) ───────────────────────
        can_use_paddle, paddle_reason = self.paddleocr_adapter.is_available()
        if can_use_paddle:
            try:
                trans = await self.paddleocr_adapter.transcribe_image(image_bytes, page_num=page_num)
                if trans.status != "provider_unavailable":
                    _, _, is_acc, _ = evaluate_transcription_quality(trans.text, trans.confidence)
                    if is_acc:
                        fallback_history.append({
                            "engine": "paddleocr",
                            "status": "success",
                            "confidence": trans.confidence,
                            "quality_score": trans.quality_score,
                        })
                        trans.status = "fallback_used" if len(fallback_history) > 1 else "success"
                        trans.fallback_history = fallback_history
                        return trans
                    else:
                        fallback_history.append({
                            "engine": "paddleocr",
                            "status": "rejected_low_quality",
                            "confidence": trans.confidence,
                            "char_count": len(trans.text),
                        })
                else:
                    fallback_history.append({
                        "engine": "paddleocr",
                        "status": "provider_unavailable",
                        "reason": paddle_reason,
                    })
            except Exception as exc:
                fallback_history.append({
                    "engine": "paddleocr",
                    "status": "failed",
                    "error_type": classify_vision_error(exc),
                    "message": str(exc),
                })
        else:
            fallback_history.append({
                "engine": "paddleocr",
                "status": "skipped",
                "reason": paddle_reason,
            })

        # ── Step 3: Tesseract (Final Local OCR Fallback) ───────────────────────
        can_use_tess, tess_reason = self.tesseract_adapter.is_available()
        if can_use_tess:
            try:
                trans = await self.tesseract_adapter.transcribe_image(image_bytes, page_num=page_num)
                if trans.text.strip():
                    fallback_history.append({
                        "engine": "tesseract",
                        "status": "success",
                        "confidence": trans.confidence,
                        "quality_score": trans.quality_score,
                    })
                    trans.status = "fallback_used" if len(fallback_history) > 1 else "success"
                    trans.fallback_history = fallback_history
                    return trans
                else:
                    fallback_history.append({
                        "engine": "tesseract",
                        "status": "failed_empty_text",
                    })
            except Exception as exc:
                fallback_history.append({
                    "engine": "tesseract",
                    "status": "failed",
                    "error_type": classify_vision_error(exc),
                    "message": str(exc),
                })
        else:
            fallback_history.append({
                "engine": "tesseract",
                "status": "skipped",
                "reason": tess_reason,
            })

        # ── Step 4: All Visual Methods Failed ─────────────────────────────────
        return PageTranscription(
            page_num=page_num,
            text="",
            extraction_source="none",
            engine="none",
            script="Latin / English",
            confidence=None,
            is_unclear=True,
            quality_score=0.0,
            status="all_visual_methods_failed",
            has_images=True,
            image_count=1,
            fallback_history=fallback_history,
            warnings=["All visual and OCR extraction attempts failed on this page."],
        )

    async def _batch_transcribe_scanned_pages(
        self,
        file_bytes: bytes,
        pages: List[PageContent],
    ) -> Dict[int, PageTranscription]:
        """
        Render non-digital pages (200 DPI JPEG) and send them to Gemini in batches of
        `vision_batch_pages`, up to 3 batches in parallel. Returns only pages whose result
        passed the quality gate; everything else is left to the per-page fallback chain.
        Never raises.
        """
        batch_size = int(getattr(self.settings, "vision_batch_pages", 4) or 0)
        if batch_size < 2 or not isinstance(self.gemini_adapter, GeminiVisionAdapter):
            return {}
        try:
            if not self.gemini_adapter.is_available()[0]:
                return {}
        except Exception:
            return {}

        todo = [p for p in pages if not (p.page_type == "digital" and not p.is_unclear and p.text.strip())]
        if len(todo) < 2:
            return {}

        rendered: List[Tuple[int, bytes]] = []
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        try:
            for p in todo:
                idx = p.page_num - 1
                if 0 <= idx < len(doc):
                    pix = doc.load_page(idx).get_pixmap(dpi=200, alpha=False)
                    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=82)
                    rendered.append((p.page_num, buf.getvalue()))
        except Exception as exc:
            logger.warning("[visual_pipeline] Page rendering for batching failed: %s", exc)
            return {}
        finally:
            doc.close()

        batches = [rendered[i:i + batch_size] for i in range(0, len(rendered), batch_size)]
        results: Dict[int, PageTranscription] = {}
        sem = asyncio.Semaphore(3)

        async def _run(batch: List[Tuple[int, bytes]]) -> None:
            async with sem:
                try:
                    got = await self.gemini_adapter.transcribe_images_batch(batch)
                except Exception as exc:
                    logger.warning(
                        "[visual_pipeline] Gemini batch (pages %s-%s) failed, will fall back per page: %s",
                        batch[0][0], batch[-1][0], exc,
                    )
                    return
                for page_num, trans in got.items():
                    _, _, acceptable, _ = evaluate_transcription_quality(trans.text, trans.confidence)
                    if acceptable:
                        trans.fallback_history = [{
                            "engine": "gemini_vision_batch",
                            "status": "success",
                            "quality_score": trans.quality_score,
                            "is_unclear": trans.is_unclear,
                        }]
                        results[page_num] = trans

        await asyncio.gather(*(_run(b) for b in batches))
        logger.info("[visual_pipeline] Batched Gemini Vision read %d/%d pages", len(results), len(rendered))
        return results

    async def process_pdf_pages(
        self,
        file_bytes: bytes,
        pages: List[PageContent],
    ) -> List[PageTranscription]:
        """
        Process all pages of a PDF document page-by-page.
        Preserves digital pages; rasterizes scanned pages and routes them to the visual waterfall.
        """
        if not pages:
            return []

        # Fast path: read scanned/handwritten pages several-per-request with Gemini Vision.
        # Pages it can't read well fall through to the normal per-page waterfall below.
        batch_results = await self._batch_transcribe_scanned_pages(file_bytes, pages)

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        transcriptions: List[PageTranscription] = []

        try:
            for idx, page in enumerate(pages):
                if page.page_type == "digital" and not page.is_unclear and page.text.strip():
                    # Native digital page bypass
                    trans = PageTranscription(
                        page_num=page.page_num,
                        text=page.text,
                        extraction_source="pymupdf",
                        engine="pymupdf",
                        script=page.script,
                        confidence=None,
                        is_unclear=False,
                        quality_score=page.quality_score,
                        status="success",
                        char_count=page.char_count,
                        word_count=page.word_count,
                        has_images=page.has_images,
                        image_count=page.image_count,
                        raw_signals=page.raw_signals,
                        fallback_history=[],
                    )
                    transcriptions.append(trans)
                else:
                    if page.page_num in batch_results:
                        transcriptions.append(batch_results[page.page_num])
                        continue
                    # Scanned or degraded page -> rasterize to 300 DPI image
                    if idx < len(doc):
                        pdf_page = doc.load_page(idx)
                        pix = pdf_page.get_pixmap(dpi=300)
                        img_bytes = pix.tobytes("png")
                    else:
                        img_bytes = b""

                    trans = await self.transcribe_page_image(
                        image_bytes=img_bytes,
                        page_num=page.page_num,
                        existing_page=page,
                    )
                    transcriptions.append(trans)
        finally:
            doc.close()

        return transcriptions

    async def process_image_file(
        self,
        file_bytes: bytes,
        filename: str = "document_image.png",
    ) -> List[PageTranscription]:
        """
        Process a standalone image file (JPG, PNG, WebP) through the visual pipeline.
        """
        # Validate format
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                img.verify()
        except Exception as exc:
            raise ValueError(f"Invalid or corrupted image file '{filename}': {exc}") from exc

        trans = await self.transcribe_page_image(
            image_bytes=file_bytes,
            page_num=1,
            existing_page=None,
        )
        return [trans]
