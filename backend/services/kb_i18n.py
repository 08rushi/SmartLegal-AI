"""
kb_i18n.py — language overlay for static knowledge-base content (Legal ID / Property /
Business hubs, checklist templates, Jan-Yojana schemes and blogs).

Runtime never translates online. Endpoints accept ``lang`` (X-Lang header or ?lang=) and call
``localize(record, namespace, lang, root=...)``, which swaps in translated strings when
available and silently falls back to the English source otherwise. Translated text comes
from, in priority order, for every string field ``k`` of a record at path ``p``:

  1. the committed overlay file  backend/data/kb_i18n/<namespace>.<lang>.json
     (flat map  "<root>.<dotted.path>" -> text, e.g. "aadhaar.services.0.description")
  2. a per-record ``translations`` dict:  {"mr": {"description": "..."}, "hi": {...}}
  3. a sibling field ``<k>_<lang>`` (e.g. ``description_mr``)
  4. the original English value

Identifier fields (``service`` is sent back by the client when creating an application)
are never replaced; their translation is added next to them as ``<k>_display``.

``backend/scripts/translate_kb_content.py`` generates the overlay files offline.
"""

from __future__ import annotations

import copy
import json
import os
from functools import lru_cache
from typing import Any, Iterator

from services.lang import normalize_lang

OVERLAY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "kb_i18n")

# Never translated (machine identifiers, links, icons, slugs).
NO_TRANSLATE_KEYS = frozenset({
    "key", "id", "icon", "slug", "scheme_code", "scheme_id", "image_url", "url", "link",
    "official_portal", "official_link", "official_portal_url", "official_links", "type_key",
    "government_level", "state_name", "category", "published_at", "created_at", "updated_at",
    # rule-engine inputs / raw JSON columns (the decoded display fields are translated instead)
    "eligibility", "summary_hindi", "eligibility_json", "benefits_json", "required_docs_json", "official_links_json",
})
# Translated for display, but the English value is kept because clients send it back as an id.
IDENTIFIER_KEYS = frozenset({"service"})


def _is_translatable_text(key: str | None, value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if key in NO_TRANSLATE_KEYS:
        return False
    s = value.strip()
    if s.startswith(("http://", "https://", "/")):
        return False
    return any(ch.isalpha() for ch in s)


def iter_translatable(node: Any, root: str = "", key: str | None = None) -> Iterator[tuple[str, str]]:
    """Yield (path, text) for every translatable string under ``node`` (used by the generator script)."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "translations" or k in NO_TRANSLATE_KEYS or (isinstance(k, str) and k.endswith(("_hi", "_mr"))):
                continue
            yield from iter_translatable(v, f"{root}.{k}" if root else str(k), k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from iter_translatable(v, f"{root}.{i}" if root else str(i), key)
    elif _is_translatable_text(key, node):
        yield root, node


@lru_cache(maxsize=32)
def _load_overlay_cached(namespace: str, lang: str, mtime: float) -> dict[str, str]:
    path = os.path.join(OVERLAY_DIR, f"{namespace}.{lang}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def load_overlay(namespace: str, lang: str) -> dict[str, str]:
    path = os.path.join(OVERLAY_DIR, f"{namespace}.{lang}.json")
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return {}
    return _load_overlay_cached(namespace, lang, mtime)


def _walk(node: Any, path: str, key: str | None, overlay: dict, lang: str) -> Any:
    if isinstance(node, dict):
        tr = node.get("translations")
        tr = tr.get(lang) if isinstance(tr, dict) else None
        out: dict[str, Any] = {}
        for k, v in node.items():
            if k == "translations" or (isinstance(k, str) and k.endswith(("_hi", "_mr")) and k[:-3] in node):
                continue
            p = f"{path}.{k}" if path else str(k)
            if k in NO_TRANSLATE_KEYS:
                out[k] = v
            elif isinstance(v, str) and _is_translatable_text(k, v):
                new = overlay.get(p)
                if new is None and isinstance(tr, dict):
                    new = tr.get(k)
                if new is None:
                    new = node.get(f"{k}_{lang}")
                if isinstance(new, str) and new.strip():
                    if k in IDENTIFIER_KEYS:
                        out[k] = v
                        out[f"{k}_display"] = new
                    else:
                        out[k] = new
                    continue
                out[k] = v
            else:
                out[k] = _walk(v, p, k, overlay, lang)
        return out
    if isinstance(node, list):
        return [_walk(v, f"{path}.{i}" if path else str(i), key, overlay, lang) for i, v in enumerate(node)]
    if isinstance(node, str) and _is_translatable_text(key, node):
        return overlay.get(path, node)
    return node


def localize(obj: Any, namespace: str, lang: str, root: str = "") -> Any:
    """Return ``obj`` with translated strings laid on top (deep copy). English -> unchanged."""
    lang = normalize_lang(lang)
    if lang == "en":
        return obj
    overlay = load_overlay(namespace, lang)
    return _walk(copy.deepcopy(obj), root, None, overlay, lang)


def localized_checklist(guidance: dict | None, root: str, namespace: str, service: str, lang: str) -> list[str] | None:
    """Documents-required list for ``service`` in ``lang`` (English fallback), or None if unknown service."""
    if not guidance:
        return None
    for i, svc in enumerate(guidance.get("services", [])):
        if str(svc.get("service", "")).lower() == str(service).lower():
            docs = list(svc.get("documents_required", []))
            if normalize_lang(lang) == "en":
                return docs
            loc = localize(guidance, namespace, lang, root=root)
            return list(loc["services"][i].get("documents_required", docs))
    return None


def split_text(text: str, max_chars: int = 1800) -> list[str]:
    """Split long text on blank lines into <= max_chars chunks (used for markdown blog bodies)."""
    parts, cur, size = [], [], 0
    for para in text.split("\n\n"):
        if cur and size + len(para) > max_chars:
            parts.append("\n\n".join(cur))
            cur, size = [], 0
        cur.append(para)
        size += len(para) + 2
    if cur:
        parts.append("\n\n".join(cur))
    return parts
