# Staging Deployment Checklist

Target layout (recommended): frontend on Vercel at `https://app.<your-domain>`, API on any container host at `https://api.<your-domain>`. **Both must be subdomains of the same registrable domain** because login uses an HttpOnly `SameSite=Lax` cookie. If you must use different domains (e.g. `*.vercel.app` + `*.onrender.com`) the cookie must become `SameSite=None; Secure` (backend change) — ask before deploying that way.

## 1. Accounts and services you need
| Item | Why |
|---|---|
| Container host for `backend/Dockerfile` (Render, Railway, Fly, VPS…) | Runs the API; the image includes Tesseract (eng/hin/mar) |
| Custom domain with subdomains `app.` and `api.` | Cookie login |
| Supabase Postgres (already exists) | `DATABASE_URL`. Use a separate staging database/branch, not production data |
| Cloudinary account | Required in production; files are stored private with signed links |
| Resend account + verified sending domain | Password-reset email |
| Groq key (required); Gemini/OpenRouter (optional) | AI providers |
| Redis (optional but recommended) | Durable analysis queue, shared rate limits. Without it, jobs run in the web process and a restart interrupts them |

## 2. Backend environment variables (host dashboard — never commit)
Required: `ENVIRONMENT=production`, `SECRET_KEY` (>= 32 random chars), `DATABASE_URL`, `ALLOWED_ORIGINS=https://app.<your-domain>` (exact origin, no trailing slash), `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `GROQ_API_KEY`, `FRONTEND_URL=https://app.<your-domain>`.
Email: `RESEND_API_KEY`, `EMAIL_FROM` (e.g. `SmartLegal <no-reply@<your-domain>>`).
Recommended: `REDIS_URL`, `SENTRY_DSN`, `ADMIN_EMAILS`, `FORWARDED_ALLOW_IPS` (your proxy's address if known).
Leave unset in production: `AUTH_RETURN_BODY_TOKEN`, `EXPOSE_RESET_TOKEN_IN_RESPONSE`, `WHATSAPP_ENABLED`, `SHADOW_ADMIN_KEY`.
Optional later: `GEMINI_API_KEY`, `GOOGLE_CLIENT_ID`, `META_WHATSAPP_*`.

## 3. Deploy steps
1. Build and deploy the backend image (`docker build -t smartlegal-api backend`). The container runs `alembic upgrade head` then starts uvicorn; if the migration fails it will not start.
2. If the staging DB was created by the app before Alembic existed and has no `alembic_version` table, run once: `alembic stamp 0005` then let the container apply 0006 (this is what was done on the dev Supabase DB).
3. Point `api.<your-domain>` at the host and confirm `https://api.<your-domain>/health` returns 200.
4. In Vercel set `VITE_API_BASE_URL=https://api.<your-domain>` (and `VITE_GOOGLE_CLIENT_ID` only if Google sign-in is enabled), then deploy the frontend (`vercel.json` already builds `frontend/`).
5. If using Google sign-in add `https://app.<your-domain>` to the OAuth client's authorized origins; otherwise hide the button.
6. Optional worker (needs `REDIS_URL`): run the same image with command `arq worker.WorkerSettings`.

## 4. Smoke test
```bash
cd backend
python scripts/staging_smoke_test.py --api https://api.<your-domain> --origin https://app.<your-domain> --create-user
# add --with-analysis to also run one real analysis (uses AI quota)
```
The script checks health, CORS (allowed and foreign origin), 401s, no reset-token leak, cookie login, no `access_token` in the response body, foreign-origin cookie POST refused (403), upload, private download link, no `file_url` exposure, logout. It leaves one throw-away account in the staging DB — delete it.

## 5. Manual checks the script cannot do
- Open the site, switch Marathi / Hindi / English on every main page, check fonts load (no requests to Google Fonts).
- Register, log in, refresh the page (session must persist), log out.
- Upload a PDF and a photo of a document, run analysis, switch language on the Analysis page, export PDF (Hindi/Marathi use the print dialog → "Save as PDF"; check the output visually).
- Ask a chat question and an advisor question in Marathi; answers should be Marathi.
- Forgot password: email arrives, link opens the reset page, the new password works, the link is single-use.
- Hubs (Legal ID / Property / Business), Jan-Yojana, Knowledge Base, My Documents download link.

## 6. Known gaps in this deployment
- Hub and Jan-Yojana database content stays English in Hindi/Marathi mode (translation script not run).
- Documents created during local development are stored locally and will not exist in staging.
- Gemini analysis and Google OAuth are unverified; WhatsApp is off.
- Rate limits are per-process unless Redis-backed limits are added.
- Hindi/Marathi translations need review by a native speaker before launch.
