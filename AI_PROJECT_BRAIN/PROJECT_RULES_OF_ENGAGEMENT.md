# SmartLegal-AI Project Rules of Engagement

These rules protect the working product while SmartLegal-AI evolves. Follow them before changing upload, analysis, AI, auth, Redux, prompts, or legal guidance behavior.

Live code is the source of truth. Historical PDFs and docs are baseline context only.

## 1. Upload Flow Rules

Protected files:
- `frontend/src/pages/Upload.tsx`
- `frontend/src/store/documentSlice.ts`
- `backend/routers/upload.py`

Rules:
- Do not break the sequence: preview -> upload -> analyze -> navigate to `/analysis/:documentId`.
- Preserve upload progress reporting.
- Preserve file preview UX unless replacing it with a better equivalent.
- Keep backend file validation stronger than extension checks.
- Do not claim image analysis works unless the backend actually supports OCR/image parsing.
- If accepting a file type in the frontend, the backend must support and analyze it safely.
- Preserve anonymous upload behavior only if explicitly intended; otherwise migrate with a clear auth plan.
- Keep upload size limits consistent between frontend and backend.
- Do not remove local temp fallback unless durable storage is fully configured.
- Do not expose local file paths to users in errors.

Current critical mismatch:
- Upload accepts PDF, JPEG, PNG, WebP.
- Analysis currently uses PDF-only PyMuPDF extraction.
- Fix this before marketing image uploads as supported.

## 2. Analyze Flow Rules

Protected files:
- `frontend/src/store/analysisSlice.ts`
- `frontend/src/pages/Analysis.tsx`
- `backend/routers/analyze.py`
- `backend/cache.py`
- `backend/services/pdf_parser.py`
- `backend/services/gemini_service.py`

Rules:
- Preserve deep linking through `/analysis/:documentId`.
- Preserve document recovery through `fetchDocumentById`.
- Preserve the async contract:
  - POST `/analyze` may return cached `{ analysis }`.
  - POST `/analyze` may return `{ status: "processing", document_id }`.
  - frontend polls `/analyze/{documentId}/status`.
- Do not return partial or malformed analysis objects to the frontend.
- Redis is cache only, never source of truth.
- SQLite currently remains fallback/source of truth for analysis results.
- If replacing FastAPI `BackgroundTasks`, keep the API contract backward compatible.
- Do not delete or invalidate analysis cache without authorization checks.
- Add document ownership checks before expanding analysis usage or monetization.

## 3. Groq / Gemini Integration Rules

Historical docs mention Groq/LLaMA. Current live code uses Google Gemini.

Current live AI:
- File: `backend/services/gemini_service.py`
- Provider: Google Gemini
- SDK: `google.generativeai`
- Model: `gemini-2.0-flash`
- Env var: `GEMINI_API_KEY`

Rules:
- Do not blindly follow old Groq documentation.
- Do not rewrite Gemini integration to Groq unless this is an explicit migration task.
- If Groq is reintroduced:
  - add a provider abstraction instead of mixing providers in one function body
  - document model, SDK, base URL, env vars, rate limits, and fallback behavior
  - preserve existing API response shape
  - preserve existing prompt output schema
  - preserve Redis/SQLite cache behavior
- Do not rename `gemini_service.py` casually; many imports depend on it.
- Do not change AI provider without updating:
  - README
  - MASTER_CONTEXT.md
  - CURRENT_STATE_DIFF.md
  - environment examples
  - deployment notes
  - tests/fixtures

## 4. `GEMINI_API_KEY` Legacy Naming Rules

Rules:
- Treat `GEMINI_API_KEY` as the current required key for live Gemini code.
- Do not assume it contains a Groq key.
- Do not rename it without a compatibility bridge.
- If adding multi-provider support, prefer additive env vars:
  - `AI_PROVIDER`
  - `GEMINI_API_KEY`
  - `GROQ_API_KEY`
- Keep legacy compatibility for at least one release cycle if env names change.
- Update `.env.example` and setup docs whenever env requirements change.

## 5. JSON Schema Rules

Protected contract:
- analysis result has `summary` and `clauses`
- frontend expects `document_id`, `analyzed_at`, `summary`, `clauses`
- clauses must include at minimum:
  - `id`
  - `title`
  - `original_text`
  - `plain_english`
  - `plain_hindi`
  - `risk_level`
  - `risk_score`
  - `risk_reason`
  - `clause_type`
- summary must include at minimum:
  - `document_type`
  - `parties`
  - `key_dates`
  - `overall_risk`
  - `risk_summary`
  - `total_clauses`
  - `high_risk_count`
  - `medium_risk_count`
  - `low_risk_count`

Rules:
- Do not remove existing fields from AI output.
- Add fields only in a backward-compatible way.
- Update TypeScript types when backend/AI output changes.
- Validate AI JSON before storing or rendering.
- Never depend on raw unvalidated model output for critical UI.
- If a prompt changes, test it against representative PDFs.
- If JSON parse fails, capture enough context for debugging without logging sensitive document text.

Future schema additions should be structured, not free text:
- `law_references`
- `negotiation_suggestions`
- `counter_text`
- `signing_scenarios`
- `confidence`
- `source_pages`

## 6. Hindi + English Support Rules

Rules:
- Preserve `plain_english` and `plain_hindi` in clause output.
- Do not replace Hindi with machine-translated UI strings without review for legal accuracy.
- Do not remove the English/Hindi toggle from clause cards unless replacing it with a better multilingual interface.
- Future regional language support must use structured locale files, not hardcoded scattered strings.
- Legal translations must be human-reviewed before being presented as authoritative.
- If adding voice/TTS, preserve text fallback for accessibility and reliability.

## 7. Redux Compatibility Rules

Protected files:
- `frontend/src/store/authSlice.ts`
- `frontend/src/store/documentSlice.ts`
- `frontend/src/store/analysisSlice.ts`
- `frontend/src/store/chatSlice.ts`
- `frontend/src/types/index.ts`

Rules:
- Preserve existing slice names: `auth`, `document`, `analysis`, `chat`.
- Preserve existing thunks unless replacing with a migration plan.
- Do not change `AnalysisResult`, `UploadedDocument`, or `ChatMessage` shape without updating all pages.
- Keep token persistence compatible with `sl_token` unless migrating carefully.
- Keep `/analysis/:documentId` recoverable after refresh.
- Scope chat state by document before expanding chat features.
- Do not let stale analysis or chat from one document display under another document.
- Keep error/loading states explicit.

## 8. Legal Safety Rules

Rules:
- The app provides AI-assisted legal information, not formal legal advice.
- Never use absolute claims like:
  - "you will win"
  - "this is illegal" without qualification
  - "guaranteed"
  - "court will"
- Prefer hedged legal language:
  - "may be interpreted as"
  - "could create risk"
  - "under X law, this may require"
  - "consult a qualified Indian lawyer"
- Every high-risk legal answer should push toward professional review.
- Cite specific Indian laws only when the system has a credible basis.
- Do not invent law sections.
- Do not let AI Lawyer Bot or chat provide emergency/criminal/family/property litigation guarantees.
- Keep disclaimers visible but not used as a substitute for safe behavior.
- For government/life-services guidance, link to official sources and avoid implying government authorization.
- Do not collect government fees unless legally authorized.

## 9. Phase Discipline Rules

Current discipline:
- Phase 1 foundation/security comes before new product expansion.

Rules:
- Do not build subscriptions, WhatsApp bot, life-services hubs, or mobile app before fixing ownership/security.
- Do not expand AI Lawyer Bot before legal safety framework is explicit.
- Do not add PWA upload queue before upload/analysis persistence is durable.
- Do not add regional languages before locale architecture exists.
- Do not add payments before auth, account state, and usage limits are reliable.

Recommended order:
1. Security and ownership.
2. Upload/analyze correctness.
3. Schema/type stability.
4. Persistence and migrations.
5. AI feature expansion.
6. Accessibility.
7. Monetization and bots.

## 10. Backward Compatibility Rules

Rules:
- Existing document rows must remain readable.
- Existing analysis JSON must continue rendering.
- Existing JWT users must remain valid unless an explicit migration invalidates sessions.
- Existing local `smartlegal.db` must not be destroyed or reset without explicit approval.
- Do not change route paths casually.
- If route paths change, support old and new paths temporarily.
- If env vars change, support old names temporarily.
- If analysis schema changes, handle old cached analysis gracefully.
- If storage changes, migrate old `local://` and Cloudinary URLs carefully.

## 11. Before-Merge Checklist

Before shipping any change:
- Does upload still work?
- Does analysis still work on refresh through `/analysis/:documentId`?
- Does chat still answer for the current document only?
- Are auth tokens still attached?
- Are unauthorized users blocked from private resources?
- Are old analysis JSON payloads still renderable?
- Are Hindi and English fields preserved?
- Are docs updated if behavior changed?
- Are legal disclaimers still present?
- Does the change respect current phase priorities?

