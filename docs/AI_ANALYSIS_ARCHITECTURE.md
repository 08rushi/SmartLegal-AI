# AI Analysis: How It Works, What Breaks, and the Plan (Free now → Low-cost production)

_Measured on this repo on 2026-11-11 with the project's own API keys. Provider limits/prices change — verify before relying on numbers marked "≈"._

## 1. Current flow (what the code does)
```
Upload (≤25 MB, ≤50 pages) → POST /analyze → ARQ job (or inline task without Redis)
 1 Inspect + optimize PDF (lossless / image downsample / page split)
 2 Extract text per page (PyMuPDF)                      ← text PDFs stop here
 3 Scanned / low-quality pages → OCR waterfall, ONE PAGE AT A TIME:
     Gemini Vision → PaddleOCR (not installed) → Tesseract (12 languages at once)
 4 Chunk text (~2k tokens) → Groq, chunks run SEQUENTIALLY → clauses JSON
 5 One summary call → validate → save (DB + Redis) → UI polls /status
```

## 2. Why big documents and handwriting fail (evidence, not guesses)
| # | Finding | Evidence |
|---|---|---|
| 1 | **Groq free tier = 8,000 tokens/minute** (+ a daily cap). One 2k-token chunk costs ~5–8k tokens, so ≈ **1 chunk per minute**. | Groq response headers; real run: an ~8-page doc took 8–9 min |
| 2 | Old code treated a full window as a *failure* ("rate-limited or in cooloff") instead of waiting → chunks lost → "Analysis timed out" / "All chunks failed". | `analyses` error history in both DBs |
| 3 | `gpt-oss-120b` is a reasoning model; at default effort 25 short clauses hit `finish=length` → **JSON cut off mid-way** → "couldn't extract any clauses". | direct API test |
| 4 | Fixed 10-minute timeout for every document size (UI polled only 10 min). | `analysis_timeout_seconds=600` |
| 5 | **Your Gemini key has no free tier** (HTTP 403 "free tier is not available for this project"). So Gemini Vision — the only free path that can read handwriting — never works. | live API call |
| 6 | Tesseract cannot read handwriting; PaddleOCR isn't installed (and is configured English-only). Result: handwritten pages → "not enough readable text". | code + `requirements.txt` |
| 7 | Vision runs 1 page per call at 300 DPI PNG (multi-MB per page) — slow and quota-hungry. | `vision_pipeline.py` |
| 8 | Chat sends only the first 12,000 characters of a document → can't answer about later pages. | `chat_prompt` |

## 3. What was fixed in code (free, already applied)
- Pacing: wait up to 75 s for the rate-limit window instead of failing the chunk.
- `reasoning_effort=low` for analysis calls (no more truncated JSON); summary budget raised.
- **Compact mode** for documents > ~6k tokens: shorter clauses, no Hindi text (UI hides the Hindi tab when absent) → ~40% fewer tokens.
- **Size-aware timeouts**: `120 s + 90 s/page`, capped at 1 h; reaper/status/UI honour it.
- `GROQ_TPM_LIMIT=7500` so the local pacer matches Groq's real limit.
- Verified live: 70-clause, ~11k-token contract → 6/6 chunks, valid summary (before: lost chunk + failed summary).

**Honest free-tier ceiling:** a 50-page text document ≈ 40k tokens ≈ **20–35 min** on Groq alone and uses ~half of the daily cap (**≈ 1–2 big documents/day**). 25 MB *scanned* or handwritten files are not realistic on free tiers without a working vision key.

## 4. Free plan (₹0) — do in this order
1. **New Gemini key** at aistudio.google.com → "Create API key" → *Create in new project* (your current project has billing/free-tier disabled). Set `GEMINI_VISION_MODEL=gemini-3.5-flash-lite` (already in the model registry) or a 2.5 model if you decide to allow it (the registry test currently forbids 2.5). This alone enables scans + handwriting (rate-limited).
2. Add **free high-throughput text providers** as extra fallbacks (sign up, paste key): Cerebras and Mistral both advertise far larger free token allowances than Groq (≈ 1M tokens/day / large per-minute limits — verify); OpenRouter `:free` models as a last resort. Needs one small generic OpenAI-compatible adapter (~100 lines) next to `openrouter_service.py`.
3. **Batch OCR pages** (4–8 pages per Gemini request, JPEG ~200 DPI) → a 50-page scan = ~8 calls instead of 50.
4. **Progress + partial results**: expose `stage` and "section 7 of 20" in `/status`; show clauses already extracted if a daily cap hits.
5. Chat on long documents: pick the most relevant chunks (keyword/BM25) instead of "first 12k chars".
6. Tesseract: default to `eng+hin+mar` (12 languages at once is slow and less accurate), run pages in parallel.

## 5. Best paid flow (very low cost) — use this in production
**One provider, one big-context model: Gemini Flash-Lite / Flash on the paid tier** (already integrated for vision; 1M-token context; JSON-schema output; best handwriting quality of the options here).
```
Upload → hash/dedupe → store (private bucket, signed URLs)
  │
  ├─ Text PDF  → PyMuPDF text ─────────────┐
  └─ Scan/handwriting → render pages (200 DPI JPEG) → Gemini Flash-Lite,
        4–8 pages per request, parallel ×4, [UNCLEAR] for illegible parts ─┤
                                                                            ▼
              Gemini Flash-Lite, schema-constrained JSON:
              whole doc in 1–3 calls (map: clauses per ~100k-token part → reduce: summary)
                                                                            ▼
              validate → verified-statute enrichment → save → UI (progress via SSE/polling)
Fallbacks: Groq/Cerebras (free) for chat & short docs · human-review CTA for low-confidence/handwritten
```
Why this is better: no 20-chunk sequential loop, no token-per-minute starvation, one billing relationship, handwriting + scans + analysis on the same model.

**Approximate cost** (≈ at 2025–26 list prices; verify): Flash-Lite is about $0.10 / 1M input and $0.40 / 1M output tokens. A 50-page scanned document ≈ 65k input (images) + ~40k analysis in/out ⇒ **roughly ₹2–6 per big document**; a typical 5-page contract is a fraction of a rupee. Set a hard budget cap + per-user quota (see `billing_service`, currently an in-memory stub).

## 6. Production hardening needed with this flow
Redis/ARQ worker as a separate process (not the web server); jobs store the file *key*, not bytes (some Redis hosts reject multi-MB payloads); private object storage; per-user daily page quota; retry only on transient errors; keep `PRIVACY_MODE` option for local-only.
