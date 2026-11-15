"""
Speech-to-text for the voice feature (speak a question -> transcribe -> ask AI).

Audio is handled purely in memory: never written to disk, never logged.
"""

import io
import logging
import wave
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from config import get_settings
from limiter import limiter
from routers.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_BYTES = 10 * 1024 * 1024
MAX_SECONDS = 60
MIN_BYTES = 1000  # anything smaller cannot contain real speech
LANGUAGES = ("mr", "hi", "en")
GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

# Short vocabulary hint for Whisper; only sent for mr/hi where it helps.
LEGAL_PROMPT = "rent agreement, tenant, landlord, notice, FIR, 7/12 utara, Aadhaar, GST"

ALLOWED_CONTENT_TYPES = {
    "audio/webm", "video/webm", "audio/ogg", "application/ogg", "audio/opus",
    "audio/mp4", "video/mp4", "audio/x-m4a", "audio/m4a", "audio/aac",
    "audio/wav", "audio/x-wav", "audio/wave", "audio/vnd.wave",
    "audio/mpeg", "audio/mp3", "audio/x-mpeg",
}

_EXT = {"webm": "webm", "ogg": "ogg", "mp4": "mp4", "wav": "wav", "mp3": "mp3"}


def _sniff(data: bytes) -> Optional[str]:
    """Return container kind from magic bytes, or None if not an allowed audio container."""
    if data[:4] == b"\x1a\x45\xdf\xa3":
        return "webm"
    if data[:4] == b"OggS":
        return "ogg"
    if data[4:8] == b"ftyp":
        return "mp4"
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "wav"
    if data[:3] == b"ID3" or (len(data) > 1 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        return "mp3"
    return None


def _wav_duration(data: bytes) -> Optional[float]:
    try:
        with wave.open(io.BytesIO(data)) as w:
            rate = w.getframerate()
            return round(w.getnframes() / rate, 2) if rate else None
    except Exception:
        return None


async def _call_groq_stt(data: bytes, filename: str, content_type: str,
                         language: Optional[str], api_key: str, model: str) -> dict:
    """Call Groq Whisper. Returns the verbose_json dict. Raises httpx errors."""
    form = {"model": model, "response_format": "verbose_json", "temperature": "0"}
    if language in ("mr", "hi"):
        form["prompt"] = LEGAL_PROMPT
    if language in LANGUAGES:
        form["language"] = language
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            GROQ_STT_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            data=form,
            files={"file": (filename, data, content_type)},
        )
        resp.raise_for_status()
        return resp.json()


@router.get("/capabilities")
async def capabilities():
    return {
        "stt": bool(get_settings().groq_api_key),
        "languages": list(LANGUAGES),
        "max_seconds": MAX_SECONDS,
        "max_bytes": MAX_BYTES,
    }


@router.post("/transcribe")
@limiter.limit("20/minute")
async def transcribe(
    request: Request,
    audio: UploadFile = File(...),
    language: Optional[str] = Form(default=None),
    current_user=Depends(get_current_user),
):
    settings = get_settings()
    lang = (language or "").strip().lower()
    lang = lang if lang in LANGUAGES else None

    data = await audio.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Audio is too large. Maximum allowed size is 10 MB.")
    if not data:
        raise HTTPException(status_code=400, detail="No audio file was received.")

    ctype = (audio.content_type or "").split(";")[0].strip().lower()
    kind = _sniff(data)
    if ctype not in ALLOWED_CONTENT_TYPES or kind is None:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format. Please use webm, ogg, mp4, m4a, wav or mp3.",
        )
    if len(data) < MIN_BYTES:
        raise HTTPException(status_code=400, detail="The audio is empty or too short. Please record again.")

    duration = _wav_duration(data) if kind == "wav" else None
    if duration is not None and duration > MAX_SECONDS + 1:
        raise HTTPException(status_code=400, detail="Audio is too long. Please keep it under 60 seconds.")

    if not settings.groq_api_key:
        raise HTTPException(
            status_code=503,
            detail="Speech recognition is temporarily unavailable. Please try again later.",
        )

    try:
        result = await _call_groq_stt(
            data, f"audio.{_EXT[kind]}", ctype, lang,
            settings.groq_api_key, settings.groq_stt_model,
        )
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        logger.warning("[voice] STT provider HTTP %s", status)
        if status == 429:
            raise HTTPException(status_code=429, detail="Speech recognition is busy. Please try again in a moment.")
        raise HTTPException(
            status_code=502,
            detail="Speech recognition is temporarily unavailable. Please try again later.",
        )
    except Exception as exc:
        logger.warning("[voice] STT failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail="Speech recognition is temporarily unavailable. Please try again later.",
        )

    text = str((result or {}).get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="We could not hear anything clear. Please speak again.")

    detected = str((result or {}).get("language") or "").strip().lower()
    names = {"marathi": "mr", "hindi": "hi", "english": "en"}
    detected = names.get(detected, detected)
    out_lang = lang or (detected if detected in LANGUAGES else None)

    dur = (result or {}).get("duration")
    try:
        dur = round(float(dur), 2) if dur is not None else duration
    except (TypeError, ValueError):
        dur = duration

    return {"text": text, "language": out_lang, "duration_seconds": dur}
