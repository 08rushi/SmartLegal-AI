# SmartLegal-AI Current State Diff

Purpose: track everything that has changed since the original PDFs/documentation. Live code is the source of truth; historical docs are baseline only.

Last updated from audit: 2026-05-14.

## Baseline

Original documented system described:
- React 18 + TypeScript + Vite frontend.
- Redux Toolkit with auth, document, analysis, and chat slices.
- FastAPI backend with SQLite.
- PyMuPDF PDF text extraction.
- JWT auth existed in backend.
- Login/Register frontend pages were UI-only stubs.
- Axios auth interceptors were disabled/commented.
- Upload/analyze/chat effectively used anonymous user context.
- AI service was documented as Groq LLaMA 3.3 through an OpenAI-compatible API, despite filename `gemini_service.py`.
- `GEMINI_API_KEY` was documented as a legacy Groq key name.
- Analysis flow was documented as synchronous request/response.
- Document history was planned or in-memory only.
- Compare page was planned as side-by-side comparison.
- Deployment target was Vercel frontend + Render backend.
- File storage was local temp or Cloudinary.

## Current Reality

Live code now shows:
- AI provider is Google Gemini through `google.generativeai`, model `gemini-2.0-flash`.
- Email/password Login/Register pages are wired to Redux.
- JWT persistence is active through `localStorage` key `sl_token`.
- Axios attaches Bearer token on requests and clears token on 401.
- Upload uses optional JWT and falls back to anonymous user.
- Upload validates file content by magic bytes, not just extension.
- Upload accepts PDF, JPEG, PNG, and WebP.
- Analysis is asynchronous: POST starts or returns cached analysis, frontend polls status endpoint.
- Analysis cache hierarchy exists: Redis optional L1, SQLite L2, Gemini on miss.
- My Documents page exists.
- Backend document history endpoint exists.
- Deep linking exists through `/analysis/:documentId`.
- Analysis can recover document metadata by ID.
- Skeleton screens, file preview, offline banner, and PostHog loader exist.
- Sentry initialization and AI breadcrumbs exist.
- slowapi rate limiting exists.
- India-specific law KB exists in `backend/services/indian_law_kb.py`.
- `DOCUMENT_TEMPLATES` exists in `gemini_service.py`.

## New Features

New compared to original documentation:
- `/analysis/:documentId` route.
- `GET /api/v1/upload/history`.
- `GET /api/v1/upload/{document_id}`.
- `GET /api/v1/analyze/{document_id}/status`.
- `DELETE /api/v1/analyze/{document_id}/cache`.
- Background analysis processing.
- Redis analysis caching.
- Sentry hooks and breadcrumbs.
- slowapi rate limits:
  - upload: 10/minute
  - analyze: 5/minute
  - chat: 20/minute
- Magic-byte file validation.
- File preview before analysis.
- Skeleton loading UI.
- Offline detection banner.
- PostHog helper and events.
- My Documents page.
- Google Sign-In frontend integration.
- `auth_google.py` backend file.
- Indian law KB.
- Expanded document templates.
- AI prompt requirement for Indian law citations.

## Dependency Upgrades

Backend requirements now include systems not represented in older docs:
- `slowapi==0.1.9`
- `sentry-sdk[fastapi]==2.8.0`
- `redis[asyncio]==5.0.7`
- `google-generativeai==0.5.2`

Frontend package includes:
- `react-pdf`

Root package includes:
- `@anthropic-ai/sdk`, currently not part of the live app flow.

Important dependency reality:
- Docs that reference Groq/openai SDK are outdated for current AI implementation.
- README mentions Gemini 2.5 Flash, but code uses `gemini-2.0-flash`.

## Prompt Changes

Original docs described:
- Groq LLaMA prompts.
- Chunk prompt returning clauses.
- Summary prompt returning risk overview.
- Q&A prompt with document-grounded answer.
- Hindi summary expectations in some older docs.

Current live prompts:
- `CHUNK_PROMPT` includes document type, law context, state context, document section, and strict JSON output.
- `CHUNK_PROMPT` requires:
  - every clause extracted
  - `risk_level` low/medium/high
  - `risk_score` 1-10
  - specific Indian law citation in `risk_reason`
  - `beneficial_to_user`
  - page numbers from `[Page X]`
- `SUMMARY_PROMPT` requires:
  - document type
  - parties
  - key dates
  - overall risk
  - risk summary with Indian law citations
  - high-risk clauses
  - beneficial clauses
  - user obligations
  - other party rights
  - risk counts
- `CHAT_PROMPT` requires:
  - answer from document content
  - cite clauses where possible
  - cite Indian laws where relevant
  - simple language
  - fixed disclaimer ending
  - concise 150-250 word response

Current AI additions:
- Keyword document type detection.
- `DOCUMENT_TEMPLATES`.
- Indian law context injection.
- State-specific law context injection where available.
- Chunk-level retries.
- JSON fence cleanup.
- Empty-analysis fallback.

Prompt risks:
- No formal schema validation.
- JSON parse failures are skipped chunk-by-chunk.
- AI law citations are prompt-driven, not independently verified.
- TypeScript types do not include all AI output fields.

## Pending Roadmap

Phase 1 remaining:
- Mount/fix Google OAuth backend route.
- Add ownership checks for all document/analysis/chat access.
- Decide anonymous upload/analysis policy.
- Resolve image upload vs PDF-only parser mismatch.
- Add chat history loading and user-message persistence.
- Update TypeScript AI payload types.
- Add tests.
- Add DB migrations.

Phase 2 pending:
- Deterministic India-specific legal intelligence.
- Expanded and verified state-wise legal KB.
- Negotiation suggestions.
- Counter-proposal text.
- "What happens if I sign?" scenarios.
- Structured law references and confidence metadata.

Phase 3 pending:
- Simple/Expert mode.
- Voice input/output.
- Hindi-first and regional language UX.
- i18next.
- PWA install/offline queue.
- Static FAQs/offline guidance.

Phase 4 pending:
- Legal ID Services Hub.
- Property Help Hub.
- Business License Hub.
- Progress tracker.
- Reminders and PWA notifications.
- Clear legal/authorization model for government service guidance.

Phase 5+ pending:
- Guide Bot.
- AI Lawyer Bot.
- WhatsApp bot.
- Razorpay subscriptions.
- Lawyer referrals.
- Template marketplace.
- Capacitor mobile app.
- Scam detection.

## Security Gaps

High-priority gaps:
- `GET /upload/{document_id}` is public by document ID.
- `POST /analyze` does not enforce document ownership.
- `GET /analyze/{document_id}/status` is public by document ID.
- `DELETE /analyze/{document_id}/cache` is public by document ID.
- `POST /chat` does not enforce document ownership.
- `GET /chat/{document_id}/history` is public by document ID.
- Upload accepts anonymous users and can trigger AI-cost flows.

Other gaps:
- JWT stored in localStorage.
- No refresh token or revocation model.
- No password reset.
- No durable user/session audit log.
- Local temp files can remain on disk.
- Cloudinary raw uploads are not app-level encrypted.
- Error details can expose internal file/read issues.
- Google OAuth endpoint file lacks effect until mounted; if mounted, token audience must be verified carefully.

## Breaking Risks

Risks that can break production or user trust:
- Image uploads are accepted and previewed, but analysis uses PDF-only PyMuPDF parsing.
- Migrating to PostgreSQL without migrations will break existing data.
- Assuming `DATABASE_URL` works will not change DB location because code hardcodes `smartlegal.db`.
- Trusting old Groq docs will cause wrong API key/model/client changes.
- Mounting Google OAuth without audience validation can create auth vulnerabilities.
- FastAPI `BackgroundTasks` are not durable; analysis jobs can vanish on restart/deploy.
- Local temp storage breaks multi-instance deployment.
- AI output shape can drift and break UI because schema is not enforced.
- Chat state can mix across documents if not scoped/cleared.
- Public cache deletion can erase analysis data for any known document ID.

## Deprecated Assumptions

Do not assume:
- The project is only a scaffold.
- Auth frontend is UI-only.
- Axios auth interceptors are disabled.
- AI provider is Groq.
- `GEMINI_API_KEY` is a Groq key.
- Analysis is synchronous.
- Document history is not implemented.
- Redis/Sentry/rate limiting are absent.
- Upload validation only checks extensions.
- Google Sign-In works end-to-end.
- Image upload support means image analysis works.
- Compare page is implemented.
- JWT auth means documents are private.
- `DATABASE_URL` controls the active database.
- Background analysis is durable.
- Older PDFs are operationally accurate.

