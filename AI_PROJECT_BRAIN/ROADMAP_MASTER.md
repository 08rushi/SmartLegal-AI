# SmartLegal-AI ROADMAP_MASTER.md

Purpose:
This is the definitive strategic + execution roadmap for SmartLegal-AI.

It combines:
1. Live project reality
2. Safe execution sequence
3. Product expansion vision
4. Governance discipline
5. Legal/business safety boundaries

This file is designed for:
- You
- Codex
- Claude
- ChatGPT
- Future senior developers
- Product planning

SOURCE OF TRUTH:
- Live codebase
- MASTER_CONTEXT.md
- CURRENT_STATE_DIFF.md
- PROJECT_RULES_OF_ENGAGEMENT.md

Historical PDFs = baseline only.

Last Updated:
2026-08-25

==================================================
2026-08-25 STATE UPDATE (read first)
==================================================

Major changes since 2026-05-28 audit:
- DATABASE: Live Supabase PostgreSQL 17.6 now connected and verified (local SQLite
  auto-fallback retained). Earlier "two DB access styles" bug FIXED — all routers use
  uniform asyncpg `$1` style; auth/upload/analyze were broken against the wrapper and
  are now migrated. Alembic migrations exist (0001, 0002) but drift from app
  create_tables() — reconcile.
- AI: Groq is the ONLY runtime provider; model = openai/gpt-oss-120b (llama-3.3-70b
  was decommissioned on this account). Gemini code + indian_law_kb.py are DEAD (~970 lines).
  AI output now validated by services/analysis_schema.py.
- NEW FEATURES SHIPPED: General Legal Advisor (routers/advisor.py + Advisor.tsx),
  password-reset flow (logic only, NO email delivery), session revocation
  (token_version + /logout-all), PDF export (pdfExporter.ts), Knowledge Base page
  (Compare.tsx, static — not doc comparison), orphan-job reaper, doc-text caching.
- TOP DEBT: ~2,000+ lines of dead/duplicated backend code and ~2,100 lines of
  triple-hub duplication in the frontend; no route code-splitting; two unused frontend
  deps (react-pdf, react-hook-form); missing DB indexes on all hot FKs.

==================================================
STATUS LEGEND
==================================================

- [ ] Not Started
- [~] In Progress
- [x] Completed
- [!] Blocked / Requires Product / Legal Decision
- [R] Refactor Required
- [P0] Critical Security / Trust Blocker
- [P1] Core Product Blocker
- [P2] Major UX / Product Expansion
- [P3] Scale / Monetization / Long-Term

==================================================
GOLDEN DISCIPLINE RULE
==================================================

NO Phase 2+ expansion if:
- Any P0 ownership/security blocker exists
- Upload/analyze truth is misleading
- AI schema is unstable
- Public document/privacy boundaries remain broken

“Scale only after trust.”

==================================================
SPRINT EXECUTION ORDER (MANDATORY BUILD ORDER)
==================================================

=============================================
SPRINT 0 — DOCUMENTATION & GOVERNANCE
=============================================

Goal:
Prevent documentation drift and AI/dev confusion.

Status:
[x]

Completed:
- [x] MASTER_CONTEXT.md
- [x] CURRENT_STATE_DIFF.md
- [x] PROJECT_RULES_OF_ENGAGEMENT.md
- [x] RELEASE_CHECKLIST.md
- [x] TESTING_PROTOCOL.md
- [x] ROADMAP_MASTER.md
- [x] DEVELOPMENT_LOG.md
- [x] SESSION_UPDATE_PROTOCOL.md

Required Ongoing:
- [ ] Update README to live project reality
- [ ] Update CLAUDE.md
- [ ] Replace outdated PDFs with v2 PDFs

---

=============================================
SPRINT 1 — SECURITY FOUNDATION
=============================================

Priority:
[P0]

Goal:
Protect users, trust, privacy, and future scale.

Why this sprint first:
Current live project has ownership/privacy gaps that can break user trust and create severe security issues.

Core Tasks:

## 1A. Auth Boundary Decisions
- [x] Email/password auth works (verified on Supabase 2026-08-25)
- [x] JWT persistence works
- [x] Session revocation (token_version + /logout-all)
- [~] Google frontend exists; backend mounted with aud/iss/email_verified checks
- [!] Google OAuth end-to-end UNTESTED — needs GOOGLE_CLIENT_ID + VITE_GOOGLE_CLIENT_ID
OR
- [ ] Remove/disable Google Sign-In until production-ready

Current note:
- Google OAuth backend validates aud/iss/email_verified but has never been exercised end-to-end.

## 1B. Ownership Enforcement
- [x] Secure `GET /upload/{document_id}`
- [x] Secure `POST /analyze`
- [x] Secure `GET /analyze/{document_id}/status`
- [x] Secure `DELETE /analyze/{document_id}/cache`
- [x] Secure `POST /chat`
- [x] Secure `GET /chat/{document_id}/history`

## 1C. Anonymous Policy
- [ ] Decide:
  - disable anonymous
  - limited anonymous
  - session-scoped anonymous
- [ ] Prevent AI abuse/spam

## 1D. Security Governance
- [ ] JWT review
- [ ] localStorage risk review
- [ ] route auth tests
- [ ] cross-user access tests

Definition of Done:
- User A cannot access User B anywhere
- No public document UUID abuse
- No misleading auth UI
- Release checklist ownership section passes

---

=============================================
SPRINT 2 — UPLOAD & ANALYSIS CORRECTNESS
=============================================

Priority:
[P0]

Goal:
Ensure platform truthfulness.

Why:
Current project may imply image support while analysis is PDF-centric.

## 2A. File Truth Alignment
- [x] Restrict uploads to PDF only
OR
- [ ] Build OCR/image pipeline

Current note:
- Backend accepts PDF only, and frontend upload/home copy has been aligned to PDF-only support.

## 2B. PDF Correctness
- [x] PyMuPDF dependency installed in rebuilt backend venv
- [~] PyMuPDF parse verification
- [ ] Scanned PDF error clarity
- [ ] Empty PDF detection
- [ ] Corrupt PDF safe failure

## 2C. AI Schema Stability
- [x] Backend schema validation (services/analysis_schema.py)
- [x] Frontend TypeScript parity (Clause/DocumentSummary match AI output)
- [~] Cached JSON compatibility
- [ ] Prompt regression fixtures
- [x] Frontend force-reanalyze retry path bypasses stale failed analysis rows

Definition of Done:
- No fake image promise
- No malformed AI crashes
- No false “safe” analysis from unreadable docs

---

=============================================
SPRINT 3 — PERSISTENCE & UX COMPLETION
=============================================

Priority:
[P1]

Goal:
Complete real user product loops.

## 3A. Chat
- [x] Fetch chat history
- [x] Store user messages backend-side
- [x] Scope chat by document
- [x] Clear stale chat bleed

## 3B. Documents
- [x] My Documents reliability (history, multi-select delete, reopen analyze/chat)
- [~] Better prior-analysis reopening
- [ ] Pagination planning

## 3C. Placeholder Cleanup
- [x] `/compare` repurposed as static Knowledge Base (12 articles)
- [!] Document-comparison Redux wiring still dead (uploadComparisonDocument /
      analyzeComparisonDocument / comparisonResult never dispatched) — build UI OR delete
- [ ] Remove dead code: indian_law_kb.py, Gemini funcs, unused deps (react-pdf, react-hook-form)

Definition of Done:
- Product feels complete, not prototype-fragmented

---

=============================================
SPRINT 4 — INFRASTRUCTURE READINESS
=============================================

Priority:
[P1]

Goal:
Prepare production scale.

## 4A. Database
- [ ] Migration tooling
- [ ] PostgreSQL path
- [ ] Schema versioning

## 4B. Job Reliability
- [ ] Replace BackgroundTasks with Celery/RQ
- [ ] Retry architecture
- [ ] Failure persistence

## 4C. Storage
- [ ] Durable object storage
- [ ] Encryption
- [ ] Multi-instance readiness

Definition of Done:
- Deployable beyond prototype scale

---

=============================================
SPRINT 5 — AI PRODUCT EXPANSION
=============================================

Priority:
[P2]

Goal:
Turn SmartLegal-AI from analyzer → decision assistant

## 5A.
- [ ] Negotiation suggestions

## 5B.
- [ ] “What Happens If I Sign?”

## 5C.
- [ ] Deterministic Indian law intelligence

## 5D.
- [ ] Safer AI Lawyer framework

## 5E.
- [ ] Regional strategy prep

==================================================
PHASE 2 — EXPAND CORE AI POWER
==================================================

*"Make the AI truly useful for broad Indian legal reality"*

=============================================
2A — DOCUMENT TYPE EXPANSION
=============================================

Goal:
Support broader Indian legal/court/civic docs.

Current:
[~]

Already:
- DOCUMENT_TEMPLATES
- FIR
- Court
- Divorce
- Consumer
- Insurance
- Property

Next:
- [ ] Real-world corpus tuning
- [ ] Better type confidence
- [ ] OCR for scanned docs
- [ ] State-specific specialization

---

=============================================
2B — INDIA-SPECIFIC LEGAL INTELLIGENCE
=============================================

Goal:
Replace generic legal risk with credible India-aware intelligence.

Current:
[~]

Build:
- [ ] Maharashtra rent
- [ ] Delhi rent
- [ ] Karnataka rent
- [ ] Labour law
- [ ] RBI loan
- [ ] Consumer
- [ ] Contract
- [ ] Property
- [ ] Vehicle transfer

Critical Rule:
AI may guide, not fabricate certainty.

---

=============================================
2C — NEGOTIATION SUGGESTIONS
=============================================

Goal:
Move from detection → empowerment

Build:
- [ ] Clause safer alternative
- [ ] Negotiation strategy
- [ ] Copy-ready counter text
- [ ] User leverage guidance

---

=============================================
2D — WHAT HAPPENS IF I SIGN?
=============================================

Goal:
Move from analysis → future consequence simulation

Build:
- [ ] Penalty simulation
- [ ] Rights-loss simulation
- [ ] Money-loss simulation
- [ ] Obligation map

==================================================
PHASE 3 — ACCESSIBILITY REVOLUTION
==================================================

Goal:
Mass India adoption.

=============================================
3A — SIMPLE / EXPERT MODE
=============================================

- [ ] Large-font mode
- [ ] Senior-safe UX
- [ ] Voice-first simple mode

=============================================
3B — VOICE INTERFACE
=============================================

- [ ] Hindi-first
- [ ] Native language priority
- [ ] Web speech
- [ ] TTS

=============================================
3C — REGIONAL LANGUAGE
=============================================

- [ ] Hindi
- [ ] Marathi
- [ ] Gujarati
- [ ] Tamil
- [ ] Telugu
- [ ] Bengali

Rule:
Human-reviewed legal language only.

=============================================
3D — PWA
=============================================

- [ ] Installable
- [ ] Offline
- [ ] Queue
- [ ] Rural mode

==================================================
PHASE 4 — LIFE SERVICES GUIDANCE
==================================================

Goal:
Expand from legal docs → broader legal/civic guidance

IMPORTANT:
Phase 4 initial model:
GUIDANCE PLATFORM
NOT government-authorized service center

Allowed:
- Official links
- Guidance
- Checklists
- Timelines
- Reminders

Blocked until legal review:
- Government fee collection
- Official filing claims
- Unauthorized service-center claims

Safer Monetization:
- ₹9
- ₹19
- ₹49
Flat platform convenience fees only

=============================================
4A — LEGAL ID HUB
=============================================

- [x] Aadhaar
- [x] PAN
- [x] DL
- [x] Passport
- [x] Voter
- [x] Certificates

=============================================
4B — PROPERTY HUB
=============================================

- [x] 7/12
- [x] Ferfar
- [x] Index II
- [x] Registry
- [x] Mutation

=============================================
4C — BUSINESS LICENSE HUB
=============================================

- [x] GST
- [x] FSSAI
- [x] MSME
- [x] Shop Act
- [x] IEC

=============================================
4D — TRACKER
=============================================

- [x] Checklists
- [~] Reminders
- [~] PWA notifications

Current note:
- Service applications and checklists exist across Legal ID, Property, and Business hubs.
- `/tracker` now aggregates service applications and supports browser-local reminder times/notes.
- Browser notifications are opt-in and fire while the web app is open; persistent service-worker notification scheduling is still pending.

==================================================
PHASE 5 — BOTS, COMMUNITY & BUSINESS SCALE
==================================================

Rule:
No monetization before trust + security + product correctness.

=============================================
5A — GUIDE BOT
=============================================

- [ ] Platform onboarding bot
- [ ] RAG docs

=============================================
5B — AI LAWYER BOT
=============================================

- [ ] Guidance assistant only
- [ ] Legal safety
- [ ] T&C
- [ ] Escalation to real lawyers

=============================================
5C — WHATSAPP BOT
=============================================

Only after:
- [ ] Auth
- [ ] Ownership
- [ ] Abuse prevention
- [ ] Secure uploads

=============================================
5D — MONETIZATION
=============================================

- [ ] Razorpay
- [ ] Subscription
- [ ] Lawyer referral
- [ ] Marketplace

=============================================
5E — MOBILE APP
=============================================

- [ ] Capacitor
- [ ] Android
- [ ] iOS

=============================================
5F — SCAM DETECTION
=============================================

- [ ] Fraud pattern detection
- [ ] Scam clause intelligence

==================================================
TARGET PRODUCT IDENTITY
================================================== 

SmartLegal-AI should evolve from:
“Document analyzer”

Into:
“Indian legal + civic intelligence platform”

WITHOUT breaking:
- Trust
- Safety
- Legal boundaries
- Accuracy
- Accessibility

==================================================
MANDATORY UPDATE RULE
==================================================

Whenever ANY roadmap item changes:
1. Update ROADMAP_MASTER.md
2. Update DEVELOPMENT_LOG.md
3. Update CURRENT_STATE_DIFF.md
4. Update MASTER_CONTEXT.md if architecture changed
5. Update TESTING_PROTOCOL.md if scope changed
6. Update RELEASE_CHECKLIST.md if release affected
