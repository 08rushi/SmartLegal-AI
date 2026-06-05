# SmartLegal-AI Master Context

This file is the permanent senior-developer brain for SmartLegal-AI. Treat the live codebase as the source of truth. Treat PDFs, README, CLAUDE.md, AUTH_SETUP.md, and older notes as historical context that may be outdated.

Last audited from live project files: 2026-05-28.

## Project Identity

SmartLegal-AI is an AI-powered legal document analysis platform for Indian users. Users upload legal documents, receive plain-language clause explanations, risk scoring, Indian-law-aware warnings, and document-grounded Q&A.

Target users include tenants, employees, borrowers, working professionals, senior citizens, small business owners, property agents, lawyers, students, and future government/NGO partners.

Product promise:
- Make legal documents understandable before users sign or act.
- Explain risk in simple language.
- Prioritize Indian legal context.
- Support accessibility and regional language expansion over time.
- Avoid pretending to be a lawyer or replacing professional legal advice.

## Real Architecture

Current stack:
- Frontend: React 18, TypeScript, Vite, Redux Toolkit, React Router, Axios, Tailwind CSS.
- Backend: FastAPI, Python, aiosqlite, SQLite, PyMuPDF, python-jose JWT, passlib bcrypt.
- AI: Groq via `groq`, model `llama-3.3-70b-versatile`.
- Upload storage: Cloudinary when configured, otherwise local temp files.
- Cache: SQLite persistent analysis cache plus optional Redis L1 cache.
- Monitoring: optional Sentry backend hooks.
- Rate limiting: slowapi, IP-based.
- Analytics: optional PostHog frontend loader/events.

Important architecture reality:
- This is no longer just a scaffold.
- Auth, upload, analysis, deep linking, history, chat persistence, skeletons, PostHog hooks, Redis cache, Sentry hooks, and Indian-law prompt context already exist.
- Security ownership boundaries are incomplete and must be fixed before scaling.

## Backend

Backend entry point: `backend/main.py`.

Mounted routers:
- `/api/v1/auth` -> `backend/routers/auth.py`
- `/api/v1/upload` -> `backend/routers/upload.py`
- `/api/v1/analyze` -> `backend/routers/analyze.py`
- `/api/v1/chat` -> `backend/routers/chat.py`

Startup lifecycle:
- Creates DB tables through `init_db()`.
- Initializes Redis if `REDIS_URL` is configured.
- Closes Redis on shutdown.

Cross-cutting backend systems:
- CORS uses `settings.origins_list`.
- Sentry initializes only when `SENTRY_DSN` exists.
- slowapi limiter is attached globally.

Important backend files:
- `backend/config.py`: pydantic settings. Includes `database_url`, Redis, Sentry, Cloudinary, auth, and Groq key.
- `backend/database.py`: hardcodes `DB_PATH = "smartlegal.db"` and does not actually use `DATABASE_URL`.
- `backend/cache.py`: optional async Redis cache for analysis results.
- `backend/limiter.py`: shared slowapi limiter keyed by client IP.
- `backend/auth_google.py`: Google OAuth endpoint is mounted, but token audience/client ID validation still needs hardening.

## Frontend

Frontend entry: `frontend/src/main.tsx`.

Main app routing: `frontend/src/App.tsx`.

Routes:
- `/` -> Home
- `/upload` -> Upload
- `/analysis` -> redirects to current document analysis if available
- `/analysis/:documentId` -> deep-linked analysis page
- `/chat` -> document chat workspace
- `/compare` -> currently knowledge-base placeholder
- `/login` -> Login
- `/register` -> Register
- `/documents` -> My Documents
- `*` -> Not Found

Frontend systems:
- `initPostHog()` runs at startup.
- JWT session is restored by `fetchCurrentUser()`.
- Document history is fetched after authenticated user is confirmed.
- Axios attaches `Authorization: Bearer <sl_token>` on every request.
- Axios clears token and redirects on 401 when a token existed.

UI status:
- Upload has file preview and skeleton loading.
- Analysis has skeleton loading, risk counters, clause filters, key points, and deep-link recovery.
- Chat has suggested questions and optimistic user messages.
- Layout has auth-aware nav, My Documents access, and offline banner.

## Redux

Redux store: `frontend/src/store/index.ts`.

Slices:

### authSlice

File: `frontend/src/store/authSlice.ts`.

State:
- `user`
- `token`
- `isLoading`
- `error`

Thunks:
- `loginUser`
- `registerUser`
- `loginWithGoogle`
- `fetchCurrentUser`

Persistence:
- JWT is stored in `localStorage` as `sl_token`.

Reality:
- Email/password login and registration are wired.
- Google login thunk exists, but backend route is not mounted.

### documentSlice

File: `frontend/src/store/documentSlice.ts`.

State:
- `current`
- `comparison`
- `history`
- `uploadProgress`
- `status`
- `error`

Thunks:
- `uploadDocument`
- `uploadComparisonDocument`
- `fetchDocumentHistory`
- `fetchDocumentById`

Reality:
- Document history is fetched from backend for logged-in users.
- Document-by-ID recovery powers deep links.
- Comparison thunks exist but the Compare UI does not use them yet.

### analysisSlice

File: `frontend/src/store/analysisSlice.ts`.

State:
- `result`
- `comparisonResult`
- `isLoading`
- `error`

Thunks:
- `analyzeDocument`
- `analyzeComparisonDocument`

Flow:
- POST `/analyze`.
- If cached result is returned, store immediately.
- If processing is returned, poll `/analyze/{documentId}/status` every 3 seconds.
- Timeout after 5 minutes.

### chatSlice

File: `frontend/src/store/chatSlice.ts`.

State:
- `messages`
- `isLoading`
- `error`
- `document_id`

Thunks/actions:
- `sendChatMessage`
- `addUserMessage`
- `setDocumentId`
- `clearChat`

Reality:
- User messages are added optimistically in frontend Redux.
- Backend stores both user and assistant messages under the authenticated user.
- Frontend fetches backend chat history for the active document.
- Messages are scoped/reset when changing documents.

## Upload -> Analyze -> Chat Data Flow

### Upload

1. User selects or drops file in `Upload.tsx`.
2. UI creates local preview URL.
3. User clicks Analyze Document.
4. `uploadDocument(file)` posts multipart file to `/api/v1/upload`.
5. Backend reads file bytes.
6. Backend validates:
   - non-empty file
   - max 10 MB
   - magic-byte type: PDF
   - extension/content mismatch when extension is known
7. Backend chooses user:
   - valid JWT -> user ID
   - missing/invalid token -> `anonymous`
8. Backend uploads to Cloudinary if configured, otherwise writes to local temp.
9. Backend inserts document row.
10. Frontend stores `document.current`.

### Analyze

1. Frontend dispatches `analyzeDocument(documentId)`.
2. Backend checks Redis L1 cache.
3. Backend checks SQLite `analyses` cache.
4. On cache hit, full analysis returns immediately.
5. On cache miss or `force_reanalyze`, stale cache is deleted.
6. Backend fetches document row.
7. Backend reads local or remote file bytes.
8. Backend queues FastAPI `BackgroundTasks`.
9. Background task writes `{"status": "processing"}` to SQLite.
10. Background task extracts text using PyMuPDF.
11. Background task calls Groq through `analyze_legal_document()`.
12. Result gets `document_id`, `analyzed_at`, `status = "done"`.
13. Result is saved to SQLite.
14. Document `document_type` is updated.
15. Result is cached in Redis if configured.
16. Frontend polls status until done/error.

### Chat

1. Chat page requires `document.current`.
2. User sends message.
3. Frontend appends local user message optimistically.
4. Frontend POSTs `{ document_id, question }` to `/api/v1/chat`.
5. Backend fetches document by ID.
6. Backend reads file bytes.
7. Backend extracts PDF text again.
8. Backend stores the user message in `chat_messages`.
9. Backend calls Groq Q&A prompt.
10. Backend saves assistant response to `chat_messages`.
11. Frontend appends assistant response.
12. On chat open/refresh, frontend fetches stored chat history for the active document.

## AI Prompts

Primary AI service file: `backend/services/groq_service.py`.

Shared AI helper file: `backend/services/gemini_service.py`.

Current model:
- Provider: Groq
- Model: `llama-3.3-70b-versatile`
- Temperature: 0.1
- Max output tokens: 4000 for chunk extraction, 2000 for summary, 1000 for chat.

Important:
- `gemini_service.py` remains because Groq reuses document type detection, law context, prompt builders, JSON extraction, and fallback summary helpers.
- The Gemini SDK is optional at import time; missing `google-generativeai` no longer blocks backend import.

Document templates:
- `rental_agreement`
- `employment_contract`
- `loan_agreement`
- `property_sale`
- `service_contract`
- `nda`
- `partnership_deed`
- `fir_criminal`
- `court_notice`
- `divorce_petition`
- `consumer_complaint`
- `insurance_policy`
- `franchise_agreement`
- `will_testament`
- `vehicle_transfer`
- `general`

Detection:
- Keyword scoring on first 3000 characters.
- Highest scoring document template wins.
- Falls back to `general`.

Prompt layers:
- `CHUNK_PROMPT`: extracts every clause from a chunk as JSON.
- `SUMMARY_PROMPT`: summarizes clauses, risk, dates, obligations, other-party rights.
- `CHAT_PROMPT`: answers user questions from document excerpt.

Indian law context:
- Injected via `services.indian_law_kb.get_law_context()`.
- State-specific variations can be injected through `get_state_variations()`.
- Prompt requires specific Indian law citations in risk reasons.

AI output caveats:
- JSON parsing failures for a chunk are logged and skipped.
- If all clauses fail, fallback result returns a valid empty analysis.
- No formal JSON schema validation exists.
- Frontend TypeScript types do not fully describe all prompt fields.

Future AI roadmap:
- Deterministic structured law findings.
- Negotiation suggestions.
- Counter-proposal text.
- "What happens if I sign?" scenarios.
- Confidence and citation quality metadata.
- Better scanned PDF/image OCR path.

## Database

Current DB: SQLite file `smartlegal.db`.

Tables:
- `users`
- `documents`
- `analyses`
- `chat_messages`

Important schema:

`users`
- `id`
- `name`
- `email`
- `password`
- `created_at`

`documents`
- `id`
- `user_id`
- `filename`
- `file_url`
- `file_size`
- `document_type`
- `status`
- `uploaded_at`

`analyses`
- `id`
- `document_id`
- `result_json`
- `analyzed_at`

`chat_messages`
- `id`
- `document_id`
- `user_id`
- `role`
- `content`
- `timestamp`

Critical DB facts:
- `DATABASE_URL` exists in settings but is ignored.
- There are no migrations.
- SQLite is not suitable for production scale.
- Existing local DB contains real app state, so schema changes need migration planning.

## Auth

Implemented:
- Email/password register.
- Email/password login.
- JWT creation with `sub = user_id`.
- `/auth/me` session restore.
- bcrypt password hashing.
- Frontend token persistence.
- Axios Bearer token interceptor.

Incomplete:
- Google Sign-In frontend exists.
- `auth_google.py` exists.
- Google router is not mounted in `main.py`.
- No password reset.
- No refresh token or server-side session revocation.
- No route-level ownership checks for most document operations.

Security boundary reality:
- JWT exists but does not yet protect all sensitive data paths.
- Upload can be anonymous.
- Analyze/chat can be called for any known document ID.
- Document fetch by ID is public.
- Analysis status and cache deletion are public by document ID.

## Current Status

Completed or mostly complete:
- Base React/FastAPI architecture.
- Email/password JWT auth.
- Token persistence.
- Upload flow.
- File magic-byte validation.
- Local/Cloudinary storage.
- Background analysis with polling.
- Redis optional cache.
- SQLite persistent cache.
- Sentry optional monitoring.
- slowapi rate limiting.
- Deep-linked analysis pages.
- My Documents page and backend history.
- Upload preview.
- Skeleton screens.
- Offline banner.
- PostHog event hooks.
- Gemini clause extraction and Q&A.
- Indian-law-aware prompt context.
- Document type templates.

Partially complete:
- Google Sign-In.
- Chat persistence.
- Comparison analysis.
- India-specific legal intelligence.
- Analytics.
- Monitoring.

Not implemented:
- Durable job queue such as Celery/RQ.
- PostgreSQL.
- Full route authorization/ownership.
- OCR/image analysis.
- i18next regional UI.
- Simple/Expert mode.
- Voice input/output.
- PWA offline upload queue.
- Life-services guidance hubs.
- Razorpay subscriptions.
- Lawyer referral network.
- WhatsApp bot.
- Mobile app wrapper.

## Roadmap

### Phase 1 - Foundation Fixes

Goal: make what exists reliable and secure before expanding.

Priority work:
1. Mount/fix Google OAuth or remove frontend Google button until backend is ready.
2. Add ownership checks for document fetch, analysis, analysis status, cache delete, chat, chat history.
3. Decide anonymous mode policy.
4. Fix image upload mismatch by either adding OCR/image analysis or restricting to PDFs.
5. Update TypeScript types to match actual AI output.
6. Add DB migration strategy.
7. Make chat history persistent end-to-end.
8. Normalize docs and comments from Groq to Gemini.
9. Add tests for auth/upload/analyze flow.

### Phase 2 - Expand Core AI Power

Planned:
- Broader Indian document type handling.
- Stronger legal KB with state-specific rent, labor, consumer, property, loan, vehicle, and court references.
- Structured law citations.
- Negotiation suggestions.
- Counter-text generation.
- Real-world consequence scenarios.

Current state:
- `DOCUMENT_TEMPLATES` exists.
- `indian_law_kb.py` exists.
- Prompt asks for citations.
- No structured negotiation/scenario UI or types yet.

### Phase 3 - Accessibility Revolution

Planned:
- Simple/Expert mode.
- Hindi-first voice interface.
- Regional language UI through i18next.
- PWA install/offline mode.
- Static FAQ/offline guidance for common document types.

Current state:
- Not implemented except current Hindi clause text from AI output, offline banner, and browser-local service reminder notifications on `/tracker`.

### Phase 4 - Life Services Guidance

Planned:
- Legal ID Services Hub.
- Property Help Hub.
- Business License Hub.
- Progress tracker and reminders.

Current state:
- Legal ID, Property, and Business License hubs are implemented as guidance-first service hubs.
- Each hub has authenticated application tracking and checklist persistence through its own backend router/table pair.
- `/tracker` aggregates all three service application types and provides browser-local reminder dates/notes.
- Browser notifications are opt-in and checked while the app is open; full PWA/service-worker notification scheduling remains future work.

Important legal/product caution:
- Provide guidance and official links first.
- Do not represent the platform as an authorized government service center unless actually licensed/authorized.
- Government fees should be paid directly on official portals unless the business has authority to collect.
- Platform guidance fee should be separate, transparent, minimal, and not disguised as government fee.

### Phase 5 - Bots and Community

Planned:
- Guide Bot.
- AI Lawyer Bot with safety framework and disclaimers.
- WhatsApp bot through Twilio.
- Voice-note summaries.
- Shareable cards/PDF summaries.

Current state:
- Chat exists only as document Q&A page.

### Monetization / Later Platform

Planned:
- Razorpay subscriptions.
- Lawyer referrals.
- Template marketplace.
- Mobile app via Capacitor.
- Scam detection.

Current state:
- Not implemented.

## Risks

### Security Risks

High:
- Public document lookup by UUID.
- Public analysis status by UUID.
- Public cache deletion.
- Public chat on any document ID.
- No ownership checks in analyze/chat flows.
- Anonymous upload/analysis can burn AI quota.

Medium:
- JWT in localStorage.
- Local temp files persist outside app cleanup.
- Raw Cloudinary uploads are not app-encrypted.
- No server-side session revocation.
- No password reset.
- CORS must be tightly configured in production.
- Error messages may leak internals.

### Product Risks

- Image uploads are advertised but analysis is PDF-only.
- AI citations may sound authoritative without deterministic verification.
- Legal guidance must avoid absolute predictions or lawyer-like guarantees.
- Life-services guidance may create regulatory/authorization confusion.

### Technical Risks

- SQLite and local files block horizontal scaling.
- FastAPI BackgroundTasks are not durable.
- No migrations.
- AI output schema drift can break UI.
- Redis is optional and not source of truth.
- Chat re-extracts full document every question.

## Rules

Always follow these project rules:

1. Live code is source of truth.
2. PDFs and older docs are historical baseline only.
3. Do not assume Groq is used; current AI code uses Gemini.
4. Do not assume Google Sign-In works until router is mounted and tested.
5. Do not assume JWT means document privacy; ownership checks are incomplete.
6. Do not add roadmap features before fixing core security and data boundaries.
7. Do not introduce legal claims without disclaimers and source/citation strategy.
8. Do not collect or imply collection of government fees unless legally authorized.
9. Do not make DB schema changes without migration/backward-compat thinking.
10. Do not expand image upload promises unless OCR/image analysis is implemented.

## Safe Modification Principles

Before editing:
- Read the relevant live file.
- Check route/API contract on both frontend and backend.
- Check Redux state assumptions.
- Check DB schema impact.
- Check auth/ownership implications.
- Check whether the feature affects stored legal documents.

When modifying backend:
- Prefer explicit dependencies and typed request/response schemas.
- Add ownership checks for any document/analysis/chat access.
- Keep Redis as cache only, never source of truth.
- Avoid long-running request threads.
- Add error handling that does not leak secrets or local file paths.
- Keep AI failures visible through Sentry/logging and user-safe messages.

When modifying frontend:
- Keep Redux state scoped to current document.
- Avoid stale analysis/chat across document switches.
- Keep deep links recoverable.
- Add loading/error/empty states.
- Match TypeScript types to backend payloads.
- Do not show controls that call unimplemented backend routes.

When modifying AI:
- Require structured JSON outputs.
- Validate outputs before storing.
- Keep citations cautious and hedged.
- Prefer schema additions over ad hoc string parsing.
- Add tests or fixtures for representative Indian document types.

When modifying docs:
- Mark outdated historical docs clearly.
- Keep `MASTER_CONTEXT.md` updated after major architecture changes.
- Document known incomplete/security-sensitive behavior honestly.

## Sprint Priorities

### Sprint 0 - Documentation and Baseline

- Make `MASTER_CONTEXT.md` the primary source of truth.
- Mark PDFs as historical baseline.
- Update README and CLAUDE.md to match live Gemini/background/Redis/auth reality.

### Sprint 1 - Security Foundation

- Mount or disable Google OAuth.
- Add authenticated ownership checks:
  - `GET /upload/{document_id}`
  - `POST /analyze`
  - `GET /analyze/{document_id}/status`
  - `DELETE /analyze/{document_id}/cache`
  - `POST /chat`
  - `GET /chat/{document_id}/history`
- Decide anonymous upload/analysis rules.
- Add basic tests for auth and authorization.

### Sprint 2 - Upload and Analysis Correctness

- Resolve PDF-only parser vs image upload mismatch.
- Add better PDF validation with PyMuPDF open/read check.
- Add clear scanned-PDF/OCR error state.
- Add AI output schema validation.
- Update frontend types for AI fields.

### Sprint 3 - Persistence and UX Completion

- Fetch chat history on Chat page.
- Store user chat messages server-side.
- Reset/scope chat state per document.
- Improve My Documents so previous analyses can be viewed reliably.
- Finish or remove comparison placeholder.

### Sprint 4 - Infrastructure Readiness

- Add DB migration tooling.
- Prepare PostgreSQL migration path.
- Replace FastAPI BackgroundTasks with durable queue.
- Move local files to durable object storage for production.
- Add pagination for documents and chat.

### Sprint 5 - AI Product Expansion

- Add structured negotiation suggestions.
- Add "What happens if I sign?" scenarios.
- Expand and verify Indian-law KB.
- Add safer AI Lawyer Bot framework.
- Add regional language strategy after core schema is stable.

