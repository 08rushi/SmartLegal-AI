"""
ai_parser.py — Centralized AI Parsing & Validation Layer (SL-021).

Provides robust JSON parsing, Pydantic validation, malformed JSON repair,
and standardized response formatting across LLM outputs (Groq / Gemini).

Phase 1 additions
-----------------
* ``parse_ai_response`` — unified entry point that combines extraction +
  Pydantic validation.  Supports three input modes:
    1. Pre-parsed dict (already structured output from JSON Schema mode)
    2. Raw string (JSON Object mode or extraction fallback)
  Returns a validated dict via ``validate_analysis``.

* Duplicate ``_extract_json`` in gemini_service is *deprecated* in favour of
  this module.  Phase 2 will remove it.
"""

import json
import re
from typing import Any, Union
from services.analysis_schema import validate_analysis


def extract_json_from_text(raw_text: str) -> Any:
    """
    Robust JSON extraction & repair layer.
    Extracts JSON objects or arrays from LLM response text, stripping markdown code blocks,
    preambles, and fixing common trailing comma syntax issues.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Empty response received from AI model.")

    text = raw_text.strip()

    # 1. Strip markdown code fences if present (```json ... ```)
    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            text = match.group(1).strip()

    # 2. Direct JSON load attempt
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. RegEx extract object or array boundaries — try object first since
    #    legal analysis responses are always JSON objects, not bare arrays.
    obj_match = re.search(r"(\{[\s\S]*\})", text)
    if obj_match:
        candidate = obj_match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Repair trailing commas in objects
            repaired = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass

    # Fallback: bare JSON array (e.g. a list of clauses without a wrapper object)
    array_match = re.search(r"(\[[\s\S]*\])", text)
    if array_match:
        candidate = array_match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Repair trailing commas in arrays
            repaired = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass

    raise ValueError(f"Could not parse valid JSON from AI response: {text[:200]}...")


def validate_and_normalize_analysis(data: dict) -> dict:
    """Validate & normalize analysis result using canonical Pydantic schema."""
    return validate_analysis(data)


def format_chat_response(raw_answer: str) -> str:
    """Clean and enforce legal disclaimer on chat output."""
    answer = raw_answer.strip()
    disclaimer = "Note: This is AI-assisted analysis, not formal legal advice. Consult a qualified advocate before acting."
    if disclaimer not in answer:
        answer = f"{answer}\n\n{disclaimer}"
    return answer


def parse_ai_response(raw: Union[str, dict]) -> dict:
    """
    Unified AI response parser — Phase 1 entry point.

    Accepts either:
      * A ``dict`` — already parsed structured output (Groq JSON Schema mode /
        Gemini response_schema mode).  Passed directly to Pydantic validation.
      * A ``str`` — raw LLM text (JSON Object mode or free-text with embedded JSON).
        Extracted via ``extract_json_from_text`` then validated.

    Returns
    -------
    dict
        A validated ``{summary: ..., clauses: [...]}`` dict ready for persistence.

    Raises
    ------
    ValueError
        If the response cannot be parsed into a valid analysis structure (no
        usable clauses, schema mismatch, empty response, etc.).
    TypeError
        If *raw* is neither a ``str`` nor a ``dict``.
    """
    if isinstance(raw, dict):
        # Path 1: Already-parsed dict (JSON Schema Structured Output).
        # Skip text extraction; go straight to Pydantic validation.
        data = raw
    elif isinstance(raw, str):
        # Path 2: Raw string — extract JSON then validate.
        data = extract_json_from_text(raw)
        if not isinstance(data, dict):
            raise ValueError(
                f"Parsed AI response is not a JSON object (got {type(data).__name__}). "
                f"Preview: {str(data)[:200]}"
            )
    else:
        raise TypeError(
            f"parse_ai_response expects str or dict, got {type(raw).__name__}."
        )

    return validate_and_normalize_analysis(data)
