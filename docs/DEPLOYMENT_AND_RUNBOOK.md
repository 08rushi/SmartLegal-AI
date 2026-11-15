# SmartLegal AI — Production Deployment & Runbook (SL-053)

## 📌 Executive Overview
SmartLegal AI is an AI-powered legal document analysis and civic service platform tailored for Indian citizens. This document provides step-by-step instructions for local development, background worker execution, database migrations, and production cloud deployment.

---

## 🛠️ System Requirements
- **Python**: `3.12+`
- **Node.js**: `20+` & `npm 10+`
- **PostgreSQL**: `15+` (Supabase pooled or self-hosted)
- **Redis**: `7+` (L1 Cache & ARQ Job Queue)
- **LLM APIs**: Groq (`llama-3.3-70b-versatile`) & Gemini (`gemini-2.0-flash`)

---

## 🔑 Environment Variables Specification

Create `.env` in `backend/`:

```env
# ── Core Settings ────────────────────────────────────────────────────────────
APP_ENV=development                            # development | staging | production
DEBUG=true
PORT=8000
FRONTEND_ORIGINS=http://localhost:5173,http://localhost:3000

# ── Database & Cache ─────────────────────────────────────────────────────────
DATABASE_URL=postgresql://postgres.xxx:password@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
REDIS_URL=redis://localhost:6379/0

# ── Auth & Security ──────────────────────────────────────────────────────────
JWT_SECRET_KEY=super_secret_jwt_key_minimum_32_characters_long_for_security
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200              # 30 Days

GOOGLE_CLIENT_ID=your_google_oauth_client_id.apps.googleusercontent.com

# ── AI Provider Keys ─────────────────────────────────────────────────────────
GROQ_API_KEY=gsk_your_groq_api_key
GEMINI_API_KEY=AIzaSy_your_gemini_api_key
DEFAULT_AI_PROVIDER=groq                       # groq | gemini
```

---

## 🚀 How to Run Locally

### 1. Backend Server
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
- API Base URL: `http://localhost:8000`
- Swagger UI Docs: `http://localhost:8000/docs`

### 2. ARQ Background Worker
```bash
cd backend
venv\Scripts\activate
python worker.py
```

### 3. Frontend Web Client
```bash
cd frontend
npm install
npm run dev
```
- App UI: `http://localhost:5173`

---

## 🧪 Running Automated Test Suites

### Backend Pytest Suite
```bash
cd backend
venv\Scripts\python.exe -m pytest tests/ -v
```

### Frontend TypeScript & Production Build Verification
```bash
cd frontend
npm run build
```

---

## 📦 Production Deployment Strategy

1. **Backend**: Containerize using Uvicorn + Gunicorn behind AWS ALB or Render/Fly.io.
2. **PostgreSQL**: Supabase PostgreSQL with transaction pooling (`port 6543`).
3. **Redis**: Upstash Redis or ElastiCache.
4. **Frontend**: Vercel or Netlify static hosting with SPA routing rules.

### Production checklist

`ENVIRONMENT` is **fail-closed**: if unset (or anything other than `development`/`dev`/`test`/`testing`/`local`) the app behaves as production. Development conveniences (localhost CORS regex, relaxed checks, returning the password-reset token via `EXPOSE_RESET_TOKEN_IN_RESPONSE=true`) require `ENVIRONMENT=development` explicitly — set it in your local `backend/.env`.

**Auth/session settings (production):** the credential is the HttpOnly `sl_token` cookie (SameSite=Lax, `Secure` in production, default lifetime `ACCESS_TOKEN_EXPIRE_MINUTES=1440`). Cookie-authenticated POST/PUT/PATCH/DELETE requests must carry an `Origin` (or `Referer`) listed in `ALLOWED_ORIGINS`. `AUTH_RETURN_BODY_TOKEN` (default `false`, deprecated) re-adds `access_token` to login/register/google JSON bodies for legacy clients. `/auth/logout` revokes the session (bumps `token_version`).

**Private documents:** new uploads are stored in Cloudinary as `authenticated` (private) raw assets and are only reachable via `GET /api/v1/upload/{id}/download`, which returns a redirect to a ~5-minute signed URL after the ownership check; `file_url` is never returned by the API. For assets uploaded before this change run (after a DB backup) `python scripts/migrate_cloudinary_to_private.py` (dry run, counts only) and then `--apply`.

Set `ENVIRONMENT=production`. The app **refuses to start** (clear error, no secret values logged) unless:
- `SECRET_KEY` is a random string of at least 32 characters (`openssl rand -hex 32`), not a placeholder.
- `DATABASE_URL` is a Postgres URL (SQLite is rejected).
- `ALLOWED_ORIGINS` lists the real frontend origin(s) (not empty, `*`, or localhost only).
- `CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET` are set (local file storage is not durable).

Startup logs a **warning** (does not fail) when these are missing: `SENTRY_DSN`, `RESEND_API_KEY` + `EMAIL_FROM` (password-reset emails), `REDIS_URL` (cache + durable queue), or when `FRONTEND_URL` is still localhost (it is used to build links in emails).

**Schema / migrations**
- `AUTO_CREATE_SCHEMA` defaults to `true` for SQLite/dev and `false` for production + Postgres. When false, startup does not run `create_tables()`; it checks `alembic_version` against the Alembic head and aborts with "run `alembic upgrade head`" if they differ. Set it explicitly to override.
- Deploy step, before starting new app instances: `cd backend && alembic upgrade head`.
- Rehearse migrations on a copy of the production database (restore a backup/branch, run `alembic upgrade head`, smoke-test) before touching production.
