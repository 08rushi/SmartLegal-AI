# SmartLegal AI — Incremental Implementation Plan (Interactive Checklist)

This implementation plan outlines the phase-by-phase execution blueprint for transforming the SmartLegal AI platform into a production-grade, secure, scalable, highly reusable, and mobile/WhatsApp-ready system. Each task includes a status checkbox for tracking execution progress.

---

## User Review Required

> [!IMPORTANT]
> **Execution Gate:** No source code changes will be made until you give the explicit signal to start. Once approved, tasks will be implemented incrementally in exact priority order (P0 $\rightarrow$ P9), updating status checkboxes as each step is verified.

---

## Task Execution Checklist (P0 – P9)

### Phase P0: Security & Correctness (Foundational Security)
- [ ] **Task 0.1:** Add B-Tree database index on `documents(user_id)`, `chat_messages(document_id, timestamp)`, and `analyses(document_id)` in [`database.py`](file:///c:/Core/SmartLegal-AI/backend/database.py).
- [ ] **Task 0.2:** Validate raw password byte length $\le 72$ bytes in registration & password reset before bcrypt hashing in [`auth.py`](file:///c:/Core/SmartLegal-AI/backend/routers/auth.py).
- [ ] **Task 0.3:** Enforce short-lived signed URLs / tokenized download verification for Cloudinary & local PDF files in [`upload.py`](file:///c:/Core/SmartLegal-AI/backend/routers/upload.py).

### Phase P1: Production Blockers & Schema Modernization
- [ ] **Task 1.1:** Migrate `result_json` from raw `TEXT` to native PostgreSQL `JSONB` with GIN index in [`database.py`](file:///c:/Core/SmartLegal-AI/backend/database.py) & [`analyze.py`](file:///c:/Core/SmartLegal-AI/backend/routers/analyze.py).
- [ ] **Task 1.2:** Add `X-Request-ID` correlation ID middleware across all backend endpoints in [`main.py`](file:///c:/Core/SmartLegal-AI/backend/main.py).

### Phase P2: Architecture & Component Modularization
- [ ] **Task 2.1:** Modularize monolithic 69KB [`Compare.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/pages/Compare.tsx) into `PdfCompareViewer.tsx`, `ClauseDiffCard.tsx`, and `CompareToolbar.tsx`.
- [ ] **Task 2.2:** Modularize monolithic 29KB [`Analysis.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/pages/Analysis.tsx) into `RiskScoreOverview.tsx`, `PartyObligationsCard.tsx`, and `ClauseFilterBar.tsx`.

### Phase P3: Performance & Bundle Optimization
- [ ] **Task 3.1:** Implement React route code-splitting via `React.lazy` and `Suspense` in [`App.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/App.tsx).
- [ ] **Task 3.2:** Convert synchronous disk file reads to non-blocking async `asyncio.to_thread` / `aiofiles` in [`analyze.py`](file:///c:/Core/SmartLegal-AI/backend/routers/analyze.py).

### Phase P4: Reusability & Shared Abstractions
- [ ] **Task 4.1:** Abstract duplicated Civic Service Hub views into a single shared `ServiceHubLayout.tsx` component.
- [ ] **Task 4.2:** Create central `useAsyncPoll.ts` hook for robust status polling with backoff and cleanup.

### Phase P5: Testing Infrastructure
- [ ] **Task 5.1:** Create automated backend integration test suite `test_ownership.py` verifying 100% route-level data isolation.

### Phase P6: Observability & Logging
- [ ] **Task 6.1:** Configure structured JSON logging with request correlation IDs and Sentry transaction tracing in [`config.py`](file:///c:/Core/SmartLegal-AI/backend/config.py).

### Phase P7: Product Feature Polish
- [ ] **Task 7.1:** Refine PDF summary report export tool (`jspdf`) & Hindi translation rendering in [`Analysis.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/pages/Analysis.tsx).

### Phase P8: WhatsApp Bot Integration Gateway
- [ ] **Task 8.1:** Add WhatsApp Cloud API webhook router (`routers/whatsapp.py`) with HMAC signature validation, OTP account linking & Redis session state machine.

### Phase P9: Mobile Application Readiness (Capacitor)
- [ ] **Task 9.1:** Configure Capacitor mobile wrapper (`capacitor.config.json`) and native file picker / secure storage abstractions.

---

## Verification Plan

### Automated Tests
* Run backend test suite: `pytest` / `python -m unittest`
* Verify ownership checks across all 24 backend routes.

### Manual Verification
* Test upload, risk analysis cockpit, Q&A chat, comparison view, and service hub tracking.
* Verify zero regressions in UI glassmorphic design and translation toggles.
