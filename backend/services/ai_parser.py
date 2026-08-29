"""
ai_parser.py — Centralized AI Parsing & Validation Layer (SL-021).

Provides robust JSON parsing, Pydantic validation, malformed JSON repair,
and standardized response formatting across LLM outputs (Groq / Gemini).
"""

import json
import re
from typing import Any
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

    # 3. RegEx extract array or object boundaries
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
