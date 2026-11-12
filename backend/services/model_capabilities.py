"""
model_capabilities.py — Centralized Model Capability Registry (Phase 1).

Separates *static* model capabilities (context window, modalities, structured-output
support, vision, etc.) from *dynamic* provider availability and live account quotas.

Key design decisions
--------------------
* Model IDs that are fixed (e.g. Groq) are declared directly in the registry.
* Gemini model IDs are intentionally **not hardcoded** here.  The GEMINI_VISION_MODEL
  env-var is read at startup; a validation error is raised if the configured model
  name is not in the registry.  Add new Gemini models to KNOWN_GEMINI_MODELS as
  they become supported.
* No TPM/RPM or per-account quota figures are stored here — those belong in the
  ProviderBudgetManager layer.

Phase 1 public API
------------------
  get_capability(model_name) → ModelCapability | None
  get_gemini_vision_model()  → ModelCapability   (reads + validates config)
  list_models()              → list[ModelCapability]
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from config import get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ModelCapability:
    """
    Static capability descriptor for a single LLM model.

    Attributes
    ----------
    name:
        Canonical model identifier string (as used in API calls).
    provider:
        Provider short-name, e.g. ``"groq"``, ``"gemini"``, ``"openai"``.
    context_window:
        Maximum *input* tokens the model accepts in a single request.
    max_output_tokens:
        Maximum tokens the model can generate in a single response.
    modalities:
        Input modalities supported, e.g. ``["text"]``, ``["text", "image"]``.
    vision_support:
        True if the model can process image / document pages natively.
    structured_output:
        "json_schema" — model supports JSON Schema Structured Outputs (strict).
        "json_object"  — model supports basic JSON Object mode only.
        "none"         — no native JSON enforcement.
    notes:
        Optional free-text notes (not used at runtime).
    """
    name: str
    provider: str
    context_window: int
    max_output_tokens: int
    modalities: List[str]
    vision_support: bool
    structured_output: str  # "json_schema" | "json_object" | "none"
    notes: str = ""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

#: Master registry — model_name → ModelCapability.
#: Add new models here; never add account-level quota data.
_REGISTRY: Dict[str, ModelCapability] = {}


def _register(cap: ModelCapability) -> None:
    _REGISTRY[cap.name] = cap


# --- Groq models -----------------------------------------------------------

_register(ModelCapability(
    name="openai/gpt-oss-120b",
    provider="groq",
    context_window=131_072,
    max_output_tokens=16_384,
    modalities=["text"],
    vision_support=False,
    structured_output="json_schema",   # Groq supports JSON Schema Structured Outputs
    notes=(
        "Groq-hosted OSS 120B.  Supports JSON Schema Structured Outputs via "
        "response_format={type:'json_schema', json_schema:{...}, strict:true}. "
        "Fallback to json_object mode when schema is not provided."
    ),
))

_register(ModelCapability(
    name="llama-3.3-70b-versatile",
    provider="groq",
    context_window=128_000,
    max_output_tokens=32_768,
    modalities=["text"],
    vision_support=False,
    structured_output="json_schema",
    notes="Groq-hosted Llama 3.3 70B.  JSON Schema Structured Outputs supported.",
))

_register(ModelCapability(
    name="llama3-70b-8192",
    provider="groq",
    context_window=8_192,
    max_output_tokens=8_192,
    modalities=["text"],
    vision_support=False,
    structured_output="json_object",
    notes="Legacy Groq Llama3 70B — JSON Object mode only (no JSON Schema).",
))

# --- Gemini models ---------------------------------------------------------
# IMPORTANT: Do NOT hardcode obsolete Gemini model IDs (e.g. gemini-2.0-flash).
# The active Gemini model is read from GEMINI_VISION_MODEL at runtime.
# Register every *currently supported* Gemini model here so the validator can
# check it.  Add new models as they become available; remove retired ones.

#: Set of known Gemini model name prefixes accepted by this registry.
#: These are capability definitions — NOT a declaration that your API key has access.
KNOWN_GEMINI_MODELS: Dict[str, ModelCapability] = {}


def _register_gemini(cap: ModelCapability) -> None:
    _register(cap)
    KNOWN_GEMINI_MODELS[cap.name] = cap


# ---------------------------------------------------------------------------
# Current Gemini 3.x models (as of September 2026)
# ---------------------------------------------------------------------------
# NOTE: Do NOT add retired Gemini 1.5 or 2.0/2.x model IDs here.
# Gemini 1.5 (all variants) and Gemini 2.0-flash are retired (June 2026).
# Gemini 2.5 series has limited/legacy access — not recommended for new projects.
# Always add new models here when they become generally available;
# remove or comment out models once they are retired.

# Gemini 2.5 series — stable (GA), listed by the Gemini API for current keys, and the default
# for scans/handwriting + whole-document analysis.
_register_gemini(ModelCapability(
    name="gemini-2.5-flash",
    provider="gemini",
    context_window=1_048_576,
    max_output_tokens=65_536,
    modalities=["text", "image", "audio", "video"],
    vision_support=True,
    structured_output="json_schema",
    notes="Gemini 2.5 Flash — multimodal, 1M context; best price/quality for legal text + handwriting.",
))

_register_gemini(ModelCapability(
    name="gemini-2.5-flash-lite",
    provider="gemini",
    context_window=1_048_576,
    max_output_tokens=65_536,
    modalities=["text", "image"],
    vision_support=True,
    structured_output="json_schema",
    notes="Gemini 2.5 Flash-Lite — cheapest option; lighter reasoning/translation quality.",
))

_register_gemini(ModelCapability(
    name="gemini-3.8-flash",
    provider="gemini",
    context_window=1_048_576,
    max_output_tokens=8_192,
    modalities=["text", "image", "audio", "video"],
    vision_support=True,
    structured_output="json_schema",
    notes=(
        "Gemini 3.8 Flash — current workhorse model (GA September 2026). "
        "Multimodal, very large context window. "
        "Structured output via response_schema in GenerationConfig."
    ),
))

_register_gemini(ModelCapability(
    name="gemini-3.7-flash",
    provider="gemini",
    context_window=1_048_576,
    max_output_tokens=8_192,
    modalities=["text", "image", "audio", "video"],
    vision_support=True,
    structured_output="json_schema",
    notes=(
        "Gemini 3.7 Flash — predecessor to 3.8, currently supported. "
        "Multimodal with large context."
    ),
))

_register_gemini(ModelCapability(
    name="gemini-3.5-flash-lite",
    provider="gemini",
    context_window=1_048_576,
    max_output_tokens=8_192,
    modalities=["text", "image"],
    vision_support=True,
    structured_output="json_schema",
    notes=(
        "Gemini 3.5 Flash-Lite — optimised for high-volume, latency-sensitive tasks. "
        "Lower cost than 3.7/3.8."
    ),
))

# Add new Gemini models here as they become generally available.
# Example (uncomment and adjust when a new model is confirmed):
# _register_gemini(ModelCapability(
#     name="gemini-X.Y-flash",
#     provider="gemini",
#     context_window=...,
#     max_output_tokens=...,
#     modalities=["text", "image"],
#     vision_support=True,
#     structured_output="json_schema",
#     notes="Placeholder — fill in real specs once model is publicly available.",
# ))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_capability(model_name: str) -> Optional[ModelCapability]:
    """Return the ModelCapability for *model_name*, or None if unknown."""
    return _REGISTRY.get(model_name)


def list_models() -> List[ModelCapability]:
    """Return all registered ModelCapability objects."""
    return list(_REGISTRY.values())


def get_gemini_vision_model() -> ModelCapability:
    """
    Read GEMINI_VISION_MODEL from settings and return its ModelCapability.

    Raises
    ------
    EnvironmentError
        If GEMINI_VISION_MODEL is not set or is an empty string.
    ValueError
        If the configured model name is not present in KNOWN_GEMINI_MODELS.
        This catches typos and obsolete/unsupported model IDs early at startup.
    """
    settings = get_settings()
    model_name: str = getattr(settings, "gemini_vision_model", "").strip()

    if not model_name:
        raise EnvironmentError(
            "GEMINI_VISION_MODEL is not configured. "
            "Set it in your .env file to a currently supported Gemini model ID, "
            f"e.g. one of: {list(KNOWN_GEMINI_MODELS.keys())}"
        )

    cap = KNOWN_GEMINI_MODELS.get(model_name)
    if cap is None:
        raise ValueError(
            f"GEMINI_VISION_MODEL={model_name!r} is not a recognized Gemini model. "
            f"Known models: {list(KNOWN_GEMINI_MODELS.keys())}. "
            "Update model_capabilities.py to add it if it is newly released."
        )

    logger.info("[model-capabilities] Gemini vision model resolved: %r", model_name)
    return cap


# --- OpenRouter models (Phase 5 Fallback) -----------------------------------

_register(ModelCapability(
    name="meta-llama/llama-3.3-70b-instruct",
    provider="openrouter",
    context_window=131_072,
    max_output_tokens=8_192,
    modalities=["text"],
    vision_support=False,
    structured_output="json_schema",
    notes="OpenRouter Llama 3.3 70B Instruct — supports strict JSON Schema.",
))

_register(ModelCapability(
    name="mistralai/mistral-large-2407",
    provider="openrouter",
    context_window=128_000,
    max_output_tokens=8_192,
    modalities=["text"],
    vision_support=False,
    structured_output="json_schema",
    notes="OpenRouter Mistral Large 2407 — supports JSON Schema.",
))

_register(ModelCapability(
    name="qwen/qwen-2.5-72b-instruct",
    provider="openrouter",
    context_window=131_072,
    max_output_tokens=8_192,
    modalities=["text"],
    vision_support=False,
    structured_output="json_schema",
    notes="OpenRouter Qwen 2.5 72B Instruct — supports JSON Schema.",
))

_register(ModelCapability(
    name="google/gemini-flash-1.5",
    provider="openrouter",
    context_window=1_048_576,
    max_output_tokens=8_192,
    modalities=["text"],
    vision_support=False,
    structured_output="json_object",
    notes="OpenRouter Gemini Flash 1.5 — json_object mode only (text analysis fallback).",
))

#: Public reference to registry for tests and introspection
MODEL_REGISTRY: Dict[str, ModelCapability] = _REGISTRY


def verify_model_capability(
    model_name: str,
    required_context: int = 2000,
    required_structured: Optional[str] = None,
    require_vision: bool = False,
    required_structured_output: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Verify whether *model_name* is registered and satisfies the required capabilities.

    Returns:
        (is_compatible, reason)
    """
    cap = get_capability(model_name)
    if cap is None:
        return False, f"Model {model_name!r} is not in the ModelCapability registry."

    if cap.context_window < required_context:
        return (
            False,
            f"Model {model_name!r} context window ({cap.context_window}) is below required {required_context}: insufficient context window.",
        )

    if require_vision and not cap.vision_support:
        return False, f"Model {model_name!r} does not support vision modality."

    expected_struct = required_structured_output if required_structured_output is not None else required_structured
    if expected_struct and cap.structured_output != expected_struct:
        return (
            False,
            f"Model {model_name!r} only supports {cap.structured_output!r} output, but {expected_struct!r} is required (does not support structured_output).",
        )

    return True, None


def get_openrouter_model() -> str:
    """
    Read OPENROUTER_MODEL from settings, validate against registry, and return its canonical model ID string.
    """
    settings = get_settings()
    model_name = getattr(settings, "openrouter_model", "meta-llama/llama-3.3-70b-instruct").strip()
    if not model_name:
        raise EnvironmentError("OPENROUTER_MODEL is not configured.")

    valid, reason = verify_model_capability(
        model_name, required_context=2500, required_structured="json_schema"
    )
    if not valid:
        raise ValueError(f"Configured OPENROUTER_MODEL={model_name!r} is incompatible: {reason}")

    return model_name


def get_openrouter_capability() -> ModelCapability:
    """Return the ModelCapability descriptor for the configured OPENROUTER_MODEL."""
    model_name = get_openrouter_model()
    cap = get_capability(model_name)
    if cap is None:
        raise ValueError(f"Model {model_name!r} has no registered capability.")
    return cap
