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
2026-05-15

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
- [~] Email/password auth works
- [~] JWT persistence works
- [~] Google frontend exists
- [ ] Mount + verify Google OAuth backend
OR
- [ ] Remove/disable Google Sign-In until production-ready

## 1B. Ownership Enforcement
- [ ] Secure `GET /upload/{document_id}`
- [ ] Secure `POST /analyze`
- [ ] Secure `GET /analyze/{document_id}/status`
- [ ] Secure `DELETE /analyze/{document_id}/cache`
- [ ] Secure `POST /chat`
- [ ] Secure `GET /chat/{document_id}/history`

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
- [ ] Restrict uploads to PDF only
OR
- [ ] Build OCR/image pipeline

## 2B. PDF Correctness
- [ ] PyMuPDF parse verification
- [ ] Scanned PDF error clarity
- [ ] Empty PDF detection
- [ ] Corrupt PDF safe failure

## 2C. AI Schema Stability
- [ ] Backend schema validation
- [ ] Frontend TypeScript parity
- [ ] Cached JSON compatibility
- [ ] Prompt regression fixtures

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
- [ ] Fetch chat history
- [ ] Store user messages backend-side
- [ ] Scope chat by document
- [ ] Clear stale chat bleed

## 3B. Documents
- [ ] My Documents reliability
- [ ] Better prior-analysis reopening
- [ ] Pagination planning

## 3C. Placeholder Cleanup
- [ ] Compare fully implement
OR
- [ ] Remove/hide compare
- [ ] Remove dead UI paths

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

- [ ] Aadhaar
- [ ] PAN
- [ ] DL
- [ ] Passport
- [ ] Voter
- [ ] Certificates

=============================================
4B — PROPERTY HUB
=============================================

- [ ] 7/12
- [ ] Ferfar
- [ ] Index II
- [ ] Registry
- [ ] Mutation

=============================================
4C — BUSINESS LICENSE HUB
=============================================

- [ ] GST
- [ ] FSSAI
- [ ] MSME
- [ ] Shop Act
- [ ] IEC

=============================================
4D — TRACKER
=============================================

- [ ] Checklists
- [ ] Reminders
- [ ] PWA notifications

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