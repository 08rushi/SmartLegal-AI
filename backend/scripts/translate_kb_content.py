"""
translate_kb_content.py — OFFLINE generator for the Hindi / Marathi overlays of the static
knowledge base (Legal ID, Property, Business hubs incl. checklist templates, Jan-Yojana
schemes and blogs).

It walks the English source data, translates every user-visible string through the
project's AI provider pipeline (services.translation_service -> ai_orchestrator: Groq with
OpenRouter / Gemini fallback, paced for the free-tier TPM window) and writes flat JSON
overlays that are meant to be COMMITTED:

    backend/data/kb_i18n/<namespace>.<lang>.json     {"aadhaar.services.0.description": "...", ...}

At runtime services/kb_i18n.py only reads these files; there is no online translation.

Usage (from the backend directory, with a working GROQ_API_KEY etc. in .env):

    python scripts/translate_kb_content.py --dry-run                 # print counts only, no AI calls
    python scripts/translate_kb_content.py --langs mr,hi             # everything
    python scripts/translate_kb_content.py --namespaces legal_id --langs mr
    python scripts/translate_kb_content.py --max-batches 20          # stop early (resume later)

The run is resumable: strings already present in an overlay file are skipped, and the file
is rewritten after every few batches. Review the output before committing (AI translation of
legal text should be spot-checked by a native speaker). This script is NOT run automatically.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.kb_i18n import OVERLAY_DIR, iter_translatable, split_text  # noqa: E402
from services.lang import LANG_NAMES  # noqa: E402

CHUNK_CHARS = 1800
SAVE_EVERY_BATCHES = 5


def build_sources() -> dict[str, list[tuple[str, object]]]:
    """namespace -> [(root_key, record)] using the same roots the routers pass to localize()."""
    from services.business_kb import BUSINESS_KB
    from services.legal_id_kb import LEGAL_ID_KB
    from services.property_kb import PROPERTY_KB
    from services.yojana_blog_service import SEED_BLOGS
    from services.yojana_ingest import SEED_SCHEMES

    schemes = []
    for s in SEED_SCHEMES:
        rec = dict(s)
        # mirror the decoded fields the /yojana endpoints expose
        rec["benefits"] = json.loads(rec.get("benefits_json") or "[]")
        rec["required_docs"] = json.loads(rec.get("required_docs_json") or "[]")
        schemes.append((str(rec["scheme_code"]), rec))
    blogs = [(str(b["slug"]), dict(b)) for b in SEED_BLOGS]

    return {
        "legal_id": list(LEGAL_ID_KB.items()),
        "property": list(PROPERTY_KB.items()),
        "business": list(BUSINESS_KB.items()),
        "yojana_schemes": schemes,
        "yojana_blogs": blogs,
    }


def collect_units(records: list[tuple[str, object]]) -> list[tuple[str, str]]:
    units: list[tuple[str, str]] = []
    for root, rec in records:
        units.extend(iter_translatable(rec, root))
    return units


def load_overlay(path: str) -> dict[str, str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_overlay(path: str, data: dict[str, str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def print_inventory(sources) -> None:
    print(f"{'namespace':16} {'records':>8} {'strings':>8} {'chars':>9}")
    total_s = total_c = 0
    for ns, records in sources.items():
        units = collect_units(records)
        chars = sum(len(t) for _, t in units)
        total_s += len(units)
        total_c += chars
        print(f"{ns:16} {len(records):8d} {len(units):8d} {chars:9d}")
    print(f"{'TOTAL':16} {'':8} {total_s:8d} {total_c:9d}   (per language)")


async def translate_namespace(ns: str, units: list[tuple[str, str]], lang: str, max_batches: int | None) -> int:
    from services import translation_service as ts

    out_path = os.path.join(OVERLAY_DIR, f"{ns}.{lang}.json")
    overlay = load_overlay(out_path)
    todo = [(p, t) for p, t in units if p not in overlay]
    print(f"[{ns}/{lang}] {len(units)} strings, {len(overlay)} already translated, {len(todo)} to do")

    # Break long strings (blog markdown) into chunks; reassemble per path.
    chunk_units: list[tuple[str, str]] = []
    for path, text in todo:
        parts = split_text(text, CHUNK_CHARS) if len(text) > CHUNK_CHARS else [text]
        for i, part in enumerate(parts):
            chunk_units.append((f"{path}#{i}", part))
    pieces: dict[str, dict[int, str]] = {}
    expected: dict[str, int] = {}
    for key, _ in chunk_units:
        path, idx = key.rsplit("#", 1)
        expected[path] = max(expected.get(path, 0), int(idx) + 1)

    batches = ts.build_batches(chunk_units, CHUNK_CHARS)
    done_batches = 0
    for batch in batches:
        if max_batches is not None and done_batches >= max_batches:
            print(f"[{ns}/{lang}] stopping after {done_batches} batches (--max-batches); re-run to resume")
            break
        try:
            result = await ts._translate_batch(batch, lang)
        except Exception as exc:  # provider hiccup: keep what we have, resume later
            print(f"[{ns}/{lang}] batch failed ({type(exc).__name__}: {exc}); saving progress and stopping")
            break
        for key, text in result.items():
            path, idx = key.rsplit("#", 1)
            pieces.setdefault(path, {})[int(idx)] = text
            if len(pieces[path]) == expected[path]:
                overlay[path] = "\n\n".join(pieces[path][i] for i in range(expected[path]))
        done_batches += 1
        if done_batches % SAVE_EVERY_BATCHES == 0:
            save_overlay(out_path, overlay)
            print(f"[{ns}/{lang}] {done_batches}/{len(batches)} batches, {len(overlay)} strings saved")
    save_overlay(out_path, overlay)
    print(f"[{ns}/{lang}] wrote {out_path} ({len(overlay)} strings)")
    return len(overlay)


async def main() -> None:
    ap = argparse.ArgumentParser(description="Generate hi/mr KB overlays offline (not run automatically).")
    ap.add_argument("--langs", default="mr,hi", help="comma list of mr,hi")
    ap.add_argument("--namespaces", default="", help="comma list; default all")
    ap.add_argument("--dry-run", action="store_true", help="print the string inventory and exit (no AI calls)")
    ap.add_argument("--max-batches", type=int, default=None, help="stop after N AI batches per namespace/lang")
    args = ap.parse_args()

    sources = build_sources()
    if args.namespaces:
        wanted = {n.strip() for n in args.namespaces.split(",") if n.strip()}
        unknown = wanted - set(sources)
        if unknown:
            raise SystemExit(f"unknown namespace(s): {', '.join(sorted(unknown))}; choose from {', '.join(sources)}")
        sources = {k: v for k, v in sources.items() if k in wanted}

    print_inventory(sources)
    if args.dry_run:
        return

    langs = [l.strip() for l in args.langs.split(",") if l.strip()]
    for lang in langs:
        if lang not in ("mr", "hi"):
            raise SystemExit(f"unsupported lang {lang!r}; use mr and/or hi ({LANG_NAMES})")
    for lang in langs:
        for ns, records in sources.items():
            await translate_namespace(ns, collect_units(records), lang, args.max_batches)


if __name__ == "__main__":
    asyncio.run(main())
