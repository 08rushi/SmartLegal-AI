# SmartLegal AI — Claude Guidelines & Project Context

## What this project is
AI-powered legal document analyzer & civic service platform for Indian citizens. Users upload agreements, deeds, court/case files, etc. and get plain-language explanations, clause-by-clause risk scoring, and a Hindi/English toggle (plus the document's own language). Also: document Q&A, a general AI Legal Advisor, "What happens if I sign?" and negotiation insights, civic hubs (Legal ID, Property, Business, Jan-Yojana), and a WhatsApp bot.

Built on free-tier API keys for now (Groq, Gemini, OpenRouter). Production hardening comes later.

## Current Status (verified against code)
- ✅ Core loop: auth → upload → analyze (async worker, polling) → clauses/summary → chat. Ownership checks on document, analysis, chat and hub routes.
- ✅ AI pipeline: `services/gemini_analysis.py` (Gemini 2.5 Flash, whole-document, 1M context) is tried first when `GEMINI_API_KEY` is usable and `ANALYSIS_PROVIDER` is `auto`/`gemini`; on 401/403 it marks Gemini unavailable for 30 min and falls back to Groq (`GROQ_MODEL`, default `openai/gpt-oss-120b`) → OpenRouter → Gemini REST. Token-aware chunking, compact mode for long docs, paced waits for the Groq free-tier TPM window, size-aware job timeouts, stage/progress reporting (`services/progress.py` → `analysis_jobs` → `/analyze/{id}/status`), Pydantic output validation. Gemini paths are mock-tested only — the project's current Gemini key has no free tier, so they are **not verified live**.
- ✅ Chat on long documents uses `services/retrieval.py` (`select_relevant_text`, Indic-aware tokens) instead of truncating.
- ✅ Scanned docs/images/handwriting: OCR waterfall Gemini Vision (batched, `VISION_BATCH_PAGES`, default `gemini-2.5-flash`) → PaddleOCR → Tesseract (cannot read handwriting; needs Tesseract or a Gemini key; `PRIVACY_MODE` disables cloud vision).
- ✅ Hubs: Legal ID / Property / Business share `services/application_service.py` + `checklist_service.py`; Jan-Yojana scheme matcher + blogs.
- ✅ WhatsApp bot (Meta Cloud API webhook, idempotency, mr/hi/en) — verified with mocked tests; live sandbox not yet exercised.
- ✅ Phase 7 offline evaluation (`backend/evaluation/`), Phase 8 frontend confidence UX, Phase 9 shadow/canary (`backend/shadow/`, off by default).
- ⚠️ **Not real yet**: `/compare` shows sample data (preview notice shown). `billing_service`, `org_service`, `audit_service`, `analytics_service`, `ai_ops_service`, `reminder_service`, `share_service`, `admin_kb_service` are **in-memory stubs** (reset on restart); `routers/share.py` and `routers/admin.py` are **not mounted**. Password-reset emails are not sent. Google OAuth untested end-to-end. Home-page stats and some marketing copy are placeholder text.
- `docs/` and `*_plan.md` task trackers over-state completion in places — trust the code over them.

## Key Technical Decisions
- **Backend**: Python 3.12, FastAPI, `asyncpg` (Supabase Postgres) with automatic local SQLite fallback (`smartlegal.db`), optional Redis (L1 cache + ARQ job queue). Routers use asyncpg-style `$1` placeholders for both DBs.
- **Jobs**: `worker.enqueue_analysis` → ARQ queue when `REDIS_URL` is set; otherwise `asyncio.create_task` inline. A reaper marks analyses stuck in "processing" as errors.
- **Frontend**: React 18 + TypeScript + Vite + Redux Toolkit (10 slices: auth, document, analysis, chat, advisor, insights, legalId, property, business, yojana) + Tailwind/custom glass theme + React Router v6, routes lazy-loaded.
- **Auth**: JWT (HS256) sent as Bearer header **and** HttpOnly `sl_token` cookie; frontend also keeps the token in `localStorage` (`sl_token`). `token_version` enables "sign out everywhere". bcrypt passwords. Google ID-token verification via tokeninfo.
- **Uploads**: PDF + JPG/PNG/WebP, magic-byte validated, 25 MB, 50 pages, SHA-256 dedupe per user. Cloudinary when configured, else local temp file (dev only; production requires Cloudinary).
- **Schema**: created at startup by `database.create_tables()` (still runs in production) plus Alembic migrations 0001–0005 — the two can drift; treat `database.py` as the working source until this is unified.

## Required environment (backend/.env)
- `GROQ_API_KEY`, `SECRET_KEY` (**≥ 32 chars; app refuses to start in production otherwise**), `DATABASE_URL`.
- Optional: `GEMINI_API_KEY` (needs billing or a fresh AI Studio project for a free tier), `OPENROUTER_API_KEY`, `REDIS_URL`, `CLOUDINARY_*`, `GOOGLE_CLIENT_ID`, `SENTRY_DSN`, `META_WHATSAPP_*`, `ENVIRONMENT=production`.
- AI tuning: `ANALYSIS_PROVIDER` (`auto`|`gemini`|`groq`), `GEMINI_TEXT_MODEL`, `GEMINI_VISION_MODEL` (default `gemini-2.5-flash`), `VISION_BATCH_PAGES` (4), `GROQ_TPM_LIMIT`, `ANALYSIS_SECONDS_PER_PAGE` (90), `ANALYSIS_MAX_TIMEOUT_SECONDS` (3600).
- `ADMIN_EMAILS` — comma-separated; only these users may call `/yojana/ingest-notice` (everyone else gets 403).
- `WHATSAPP_ENABLED` — the WhatsApp router is mounted only when true (default off; bot is deferred).
- Production: set `ENVIRONMENT=production` and `ALLOWED_ORIGINS` (dev localhost CORS regex is disabled in production).
- `SHADOW_ADMIN_KEY` — only if you use `/internal/shadow/*`; there is no default and the API returns 403 until it is set.

## Key Documentation References
- [`docs/CHANGELOG_AND_WORK_LOG.md`](docs/CHANGELOG_AND_WORK_LOG.md) · [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · [`docs/DATABASE_ARCHITECTURE.md`](docs/DATABASE_ARCHITECTURE.md) · [`docs/AUTHENTICATION_AND_SECURITY.md`](docs/AUTHENTICATION_AND_SECURITY.md) · [`docs/PROJECT_STATUS_AND_ROADMAP.md`](docs/PROJECT_STATUS_AND_ROADMAP.md) · [`docs/DEPLOYMENT_AND_RUNBOOK.md`](docs/DEPLOYMENT_AND_RUNBOOK.md)

## How to Run

### Backend
```bash
cd backend
venv\Scripts\activate          # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# Swagger docs: http://localhost:8000/docs
# Optional durable worker (needs REDIS_URL):  arq worker.WorkerSettings
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm run build    # tsc + vite build
```

### Tests
```bash
cd backend && python -m pytest tests/ -q      # full suite is slow (~7 min); run files individually while iterating
cd frontend && npm test
```

## Working rules
- Keep ownership checks (`doc["user_id"] == current_user["id"]`) on every document/analysis/chat/hub route.
- Never hardcode secrets or add default credentials.
- Keep `plain_english` / `plain_hindi` fields and the analysis JSON contract (`summary`, `clauses`, `metadata`) backward compatible; update `frontend/src/types/index.ts` with any change.
- AI output is legal *information*, not advice — keep disclaimers and never invent statute sections.
