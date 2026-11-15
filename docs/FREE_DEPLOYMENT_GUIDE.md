# Free Deployment Guide (no custom domain, no cost)

**Design:** ONE Docker container serves both the website and the API (see root `Dockerfile`). The browser talks to a single URL such as `https://smartlegal-xxxx.onrender.com`, so the login cookie is first-party, there is no CORS, and no domain is needed. Database = Supabase (free), files = Cloudinary (free), AI = Groq (free), email = Gmail SMTP (free).

Primary host: **Render free web service**. Fallback: **Koyeb free** (same image, see section 8).

## 0. What free means here (read once)
| Limit | Effect |
|---|---|
| Render free sleeps after ~15 min idle | First visit after idle takes ~1 min to wake; show patience. Do not use ping services (Render's community calls it abuse and it burns your free hours) |
| 512 MB RAM, small CPU | Normal PDFs fine; very large scans may be slow or run out of memory |
| A restart or sleep during analysis | The running analysis is lost; just re-run it |
| Supabase free pauses after 1 week of no use | Open the Supabase dashboard and "Restore" if it happens |
| Gmail SMTP has a daily send cap | Fine for password resets |
| Free-tier terms change | Check the sign-up page for a card requirement before you start |

## 1. Accounts / keys to prepare (all free)
1. **GitHub**: the code is already in `08rushi/SmartLegal-AI`, branch `SmartLegal_AI/develop` (after you push the latest commit).
2. **Supabase**: your existing project. You need the `DATABASE_URL` that is already in `backend/.env` (copy the value; never commit it).
3. **Groq**: `GROQ_API_KEY` from `backend/.env`.
4. **Cloudinary** (cloudinary.com, free): from the dashboard copy *Cloud name*, *API key*, *API secret*. Required in production for file storage.
5. **Gmail app password** (for password-reset emails): Google Account -> Security -> turn on 2-Step Verification -> *App passwords* -> create one named "SmartLegal". You get a 16-character password. `SMTP_USER` = your Gmail address, `SMTP_FROM` = `SmartLegal <your@gmail.com>`.
6. **Render** (render.com): sign up with GitHub.

## 2. Push the code
Make sure the latest work is pushed to `SmartLegal_AI/develop` (ask Claude to commit and push the single-container changes).

## 3. Create the service on Render
1. Render dashboard -> **New +** -> **Blueprint** -> select the `SmartLegal-AI` repo -> choose branch `SmartLegal_AI/develop`.
2. Render reads `render.yaml` and shows service `smartlegal-api` on the **Free** plan.
3. Fill the secret values when asked: `DATABASE_URL`, `GROQ_API_KEY`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`. (`SECRET_KEY` is generated for you; `ALLOWED_ORIGINS` and `FRONTEND_URL` are set automatically from Render's public URL.)
4. Click **Apply**. If Render asks for a payment card for the free plan, stop and tell Claude: we switch to Koyeb or another option.
5. The first build takes about 10 to 15 minutes (it compiles the website and installs Tesseract). Watch **Logs**. A healthy start prints the Alembic step and then `Uvicorn running`.

## 4. Verify
1. Open the URL Render shows (`https://smartlegal-....onrender.com`). The site should load.
2. `https://<your-url>/health` should return `{"status":"ok", ...}`.
3. From your PC, in `backend/`:
   `python scripts/staging_smoke_test.py --api https://<your-url> --origin https://<your-url> --create-user`
   Expect all checks to pass (it leaves one `smoke-...@example.com` test user; delete it in Supabase).
4. Manual checks: register, login, refresh (stays logged in), upload a PDF, run analysis, switch Marathi/Hindi/English, ask a question by voice on your phone (voice needs HTTPS, which Render provides), forgot-password email arrives.

## 5. If something fails
| Symptom | Fix |
|---|---|
| Deploy fails with "Invalid production configuration" | The log lists exactly which env var is missing; add it in Render -> Environment and redeploy |
| Container exits at start with a migration error | Check `DATABASE_URL` (use the Supabase pooler connection string) |
| Login works but actions fail with 403 | The request Origin is not allowed: confirm the page is opened on the Render URL (not an old bookmark) |
| Upload fails | Cloudinary values wrong or missing |
| Reset email never arrives | Check Gmail app password and `SMTP_FROM`; look in spam; see Render logs for "SMTP email error" |
| First request very slow | Free instance was asleep: wait ~1 minute and retry |
| Out of memory | Try a smaller PDF; long term upgrade the plan |

## 6. Updating later
Push to `SmartLegal_AI/develop`, then in Render click **Manual Deploy -> Deploy latest commit** (auto-deploy is off on purpose).

## 7. Things that still need you
- Native-speaker review of Hindi/Marathi text.
- Gemini live check and Google sign-in (parked); WhatsApp stays off.
- Rotate the Vercel recovery codes that were committed in git history (`vercel-recovery-codes.txt`).
- Hub and Jan-Yojana database content is still English in Hindi/Marathi mode (translation script not run).

## 8. Fallback: Koyeb free
1. koyeb.com -> sign up with GitHub (check whether it asks for a card).
2. **Create Service** -> GitHub -> `SmartLegal-AI`, branch `SmartLegal_AI/develop` -> builder **Dockerfile** (root `Dockerfile`), port **8000**, instance type **Free**.
3. Add the same environment variables as in section 3 plus `ENVIRONMENT=production`, `AUTO_CREATE_SCHEMA=false`, `SECRET_KEY` (32+ random characters, e.g. from a password generator), `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`. Koyeb's public domain is detected automatically.
4. Free instances sleep after about 1 hour idle and wake in a few seconds (check Koyeb's current docs).
5. Repeat section 4.
