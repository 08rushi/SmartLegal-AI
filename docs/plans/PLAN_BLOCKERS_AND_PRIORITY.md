# Blockers & Priority Plan

| ID | Pri | Blocker | Impact | Unblock steps (small tasks) | Done when |
|---|---|---|---|---|---|
| BLK-1 | P0 | CI triggers on `main/master/develop`; branches were renamed to `SmartLegal_AI/*` | PRs/pushes get no checks | (a) edit `.github/workflows/ci.yml` branches; (b) push; (c) confirm green run | CI runs on Production and develop |
| BLK-2 | P0 | Schema drift: `database.py create_tables` vs Alembic 0001–0005 | Wrong prod schema | (a) diff both; (b) write migration 0006; (c) run Alembic at startup in production; (d) drop runtime `create_tables` there; (e) fresh-DB + upgrade test | Fresh DB and upgraded DB match |
| BLK-3 | P0 | Password-reset email never sent | Locked-out users | (a) pick provider (SMTP/Resend); (b) add `EMAIL_*` env vars; (c) send mail; (d) remove token from API response; (e) test | Reset works by email |
| BLK-4 | P0 | Fake/placeholder UI: `/compare` sample data, home stats, `4D`/`BIZ` icons, in-memory stubs | Users trust false data | (a) replace stats with real or none; (b) real icons; (c) label stub features "coming soon" or hide | No fake data visible |
| BLK-5 | PARKED (user decision 2026-11-15, revisit later) | Gemini key has no free tier; Gemini paths unverified live | Preferred model untested; Groq 8K TPM slows big docs | (a) get billed or fresh AI Studio key; (b) run text + vision live; (c) record results in docs | Live run logged |
| BLK-6 | PARKED (user decision 2026-11-15, revisit later) | Google OAuth untested end to end | Login button may fail | (a) set client IDs; (b) test signup+login; (c) fix or hide button | Works or hidden |
| BLK-7 | P1 | WhatsApp bot not run on Meta sandbox | Unknown live behavior | (a) set `META_WHATSAPP_*`; (b) follow `docs/META_WHATSAPP_SANDBOX_VERIFICATION_RUNBOOK.md`; (c) record result | Sandbox pass recorded |
| BLK-8 | P1 | Production config unchecked (SECRET_KEY ≥32, Cloudinary, `ALLOWED_ORIGINS`, Sentry) | App refuses to start / insecure | Env checklist in `docs/DEPLOYMENT_AND_RUNBOOK.md`; dry run | Staging boots |
| BLK-9 | P2 | Stub services reset on restart (billing, org, audit, analytics, ai_ops, reminder, share, admin_kb) | Data loss, false features | See PND-5 | Persisted or removed |
