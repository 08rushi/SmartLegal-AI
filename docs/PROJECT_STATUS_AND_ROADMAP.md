# SmartLegal AI — Project Status & Technical Roadmap

**Last Updated:** August 25, 2026
**Database:** Supabase PostgreSQL 17.6 (LIVE) with local SQLite auto-fallback
**LLM:** Groq only — `openai/gpt-oss-120b` (configurable via `GROQ_MODEL`)
**Overall:** ~88% MVP feature-complete; core loops (auth → upload → analyze → chat) verified working end-to-end on Supabase.

---

## 1. Architecture Snapshot

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React 18 + TS + Vite + Redux Toolkit (8 slices) + Tailwind | 47 files, ~12.3k LOC. No route code-splitting yet. |
| Backend | FastAPI (Python 3.12), asyncpg + aiosqlite fallback | 22 files, ~8.2k LOC. Uniform `$1` asyncpg-style DB access. |
| Database | Supabase PostgreSQL (11 tables) + Alembic migrations | App `create_tables` and Alembic drift slightly — needs reconciliation. |
| AI | Groq `openai/gpt-oss-120b`; PyMuPDF extraction; Pydantic output validation | Gemini code present but dead. `indian_law_kb.py` present but dead. |
| Cache | Redis L1 (optional) → DB L2 → Groq L3 | Redis also caches extracted PDF text. |
| Auth | JWT (HS256) + token-version session revocation + Google OAuth + bcrypt | localStorage `sl_token`. |
| Infra | slowapi rate limiting, Sentry (optional), Cloudinary/local storage, in-process BackgroundTasks + reaper | No durable job queue yet. |

---

## 2. Feature Status

| Feature | Status | Notes |
|---|---|---|
| Email/password auth (register/login/me) | ✅ Working | Verified on Supabase. |
| Session revocation (`/logout-all`, token_version) | ✅ Working | |
| Google OAuth sign-in | ⚠️ Built, untested | Needs `GOOGLE_CLIENT_ID` / `VITE_GOOGLE_CLIENT_ID`. |
| Password reset | ⚠️ Partial | Token logic complete; **no email delivery wired** (token printed only). |
| PDF upload (magic-byte, 10MB, Cloudinary/local) | ✅ Working | |
| Analysis pipeline (Groq, 3-tier cache, background + reaper) | ✅ Working | Output validated by `analysis_schema.py`. |
| AI output → frontend type parity | ✅ Working | `plain_english`/`plain_hindi` render; EN/HI toggle works. |
| Document chat (grounded Q&A) | ✅ Working | Re-extracts PDF each turn when Redis off (perf issue). |
| General Legal Advisor | ✅ Working | Stateless; client holds history. |
| PDF export of analysis | ✅ Working | jsPDF (`pdfExporter.ts`). |
| My Documents (history, delete) | ✅ Working | |
| Knowledge Base (`/compare`) | ✅ Working (static) | 12 hardcoded articles — NOT document comparison. |
| Legal ID / Property / Business hubs | ✅ Working | CRUD apps + checklists + guidance, per-user ownership. |
| Service Tracker | ⚠️ Partial | Aggregates apps + local reminders; **cannot change app status**. |
| Document comparison | ❌ Dead-wired | Redux thunks exist, never invoked; `/compare` shows Knowledge Base instead. |
| OCR / image documents | ❌ Not implemented | PDF-only. |
| i18n / regional UI | ❌ Not implemented | Only per-clause Hindi from AI. |

---

## 3. Known Issues (fix list)

**Backend**
- `indian_law_kb.py` (739 lines) is dead — real law context comes from a small dict in `gemini_service.py`.
- Gemini AI functions (~230 lines) dead — Groq is the only provider.
- Chat re-downloads + re-parses the PDF and re-classifies every message when Redis is off.
- New `httpx.AsyncClient` per request; SQLite fallback opens a fresh connection per query.
- Groq chunk calls run sequentially (no `asyncio.gather`).
- Reaper uses `LIKE '%...%'` full scan on `analyses.result_json`.
- Missing indexes on all hot FKs (`documents.user_id`, `chat_messages.document_id`, `*_applications.user_id`, `*_checklist_items.application_id`, `password_resets.token_hash` on the app path).
- No `ON DELETE CASCADE`; deletes cascaded in app code only.
- `create_tables` vs Alembic schema drift.

**Frontend**
- Triple-hub triplication (~3,080 lines across 12 files; ~2,100 removable).
- `react-pdf` + `react-hook-form` declared but unused (dead deps, ~1MB).
- No route code-splitting / lazy loading; jsPDF eagerly bundled.
- Decorative status selector in LegalIdDetail (never sent); Service Tracker status read-only.
- `alert()` used for checklist success/error.
- Hardcoded marketing stats; placeholder text icons (`4D`, `BIZ`).
- Accessibility gaps in modals (no role/focus-trap/Escape).

---

## 4. Pending Roadmap (checklist)

### P0 — Correctness & Trust
- [ ] Reconcile `create_tables` with Alembic; make Alembic the single source of truth.
- [ ] Add DB indexes on all hot foreign keys.
- [ ] Wire password-reset email delivery (or hide the flow).
- [ ] End-to-end test Google OAuth or disable the button.
- [ ] Auth/ownership regression test suite (pytest).

### P1 — Product Completion & Infra
- [ ] Persist extracted PDF text to DB so chat/re-analysis never re-parse.
- [ ] Replace BackgroundTasks with a durable queue (RQ/Arq/Celery) or DB-status column + reaper without `LIKE`.
- [ ] Shared `read_document_bytes()` + single httpx client.
- [ ] Make Service Tracker status editable end-to-end (send + PATCH status).
- [ ] Build the Compare UI (use existing thunks) or remove dead comparison wiring.
- [ ] Remove dead code (`indian_law_kb.py`, Gemini functions, unused deps).

### P1 — Refactors (de-duplication)
- [ ] Backend: one generic hub-router factory (~760 lines saved).
- [ ] Backend: generic KB helpers (~260 lines saved).
- [ ] Frontend: `createHubSlice` factory + shared `<ServiceHub>`/`<ServiceDetail>` (~2,100 lines saved).
- [ ] Shared `extractError()` thunk helper (~200 lines).
- [ ] Shared status-color map, `formatSize`, Google-auth hook.

### P2 — AI Power
- [ ] Wire the real Indian-law KB into prompts (deterministic citations).
- [ ] Negotiation suggestions / safer-clause alternatives.
- [ ] "What happens if I sign?" consequence simulation.
- [ ] OCR pipeline for scanned PDFs/images.

### P2 — Accessibility & Reach
- [ ] i18n framework (Hindi-first UI, then Marathi/Gujarati/Tamil…).
- [ ] Simple/Expert mode; larger-font senior mode.
- [ ] PWA (installable, offline queue).

### P3 — Scale & Monetization
- [ ] Object storage + encryption for production files.
- [ ] Pagination for documents/chat.
- [ ] Razorpay flat convenience fees; lawyer referral; WhatsApp bot.

---

## 5. Recently Completed (Aug 2026)
- Fixed the DB-driver split that broke the entire authenticated surface; unified all routers to asyncpg `$1` style (Postgres + SQLite portable).
- Connected live Supabase PostgreSQL; verified register → login → upload → analyze → persist.
- Switched Groq model to `openai/gpt-oss-120b` (old Llama model was decommissioned on this account).
- Fixed analyze-cache IDOR (ownership before cache read); background worker no longer hardcodes SQLite.
- Removed committed secrets from `config.py`; added `aiosqlite`; pinned `bcrypt==4.0.1`.
- Global UI density pass (reduced page paddings, dropzone height, compacted Upload/Analysis).
