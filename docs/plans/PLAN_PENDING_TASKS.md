# Pending Tasks Plan (already in scope, unfinished)

| ID | Pri | Task | Sub-tasks | Effort |
|---|---|---|---|---|
| PND-1 | P1 | Real document comparison (`/compare`) | (a) backend endpoint diffing two analyses by clause; (b) response schema + `types/index.ts`; (c) wire existing Redux thunks; (d) remove sample data and preview notice; (e) ownership check on both docs; (f) tests | M |
| PND-2 | P1 | Service Tracker status editing | (a) `PATCH` status endpoint with ownership check; (b) UI control; (c) remove decorative selector in LegalIdDetail; (d) tests | S |
| PND-3 | PARKED | Google OAuth verification | see BLK-6 (parked) | S |
| PND-4 | P1 | WhatsApp sandbox verification | see BLK-7 | S |
| PND-5 | P2 | Replace in-memory stubs | Reminders: table+migration+router+obligation link · Share links: table with expiry, mount `routers/share.py`, ownership · Audit/analytics: tables, hook into auth/upload · Billing/org/admin-KB: decide launch need, else delete | L |
| PND-6 | P1 | Performance & DB | (a) indexes on hot FKs; (b) async file reads; (c) remove `LIKE` scan in reaper; (d) single shared httpx client | M |
| PND-7 | P1 | Security hardening | (a) ownership regression tests on every route; (b) review cookie vs localStorage token duplication; (c) rate-limit review | M |
| PND-8 | P2 | Frontend de-duplication | (a) `createHubSlice` factory; (b) shared `ServiceHub`/`ServiceDetail`; (c) `extractError()` helper; (d) remove unused deps (`react-pdf`, `react-hook-form`); (e) replace `alert()`; (f) modal a11y (role, focus trap, Escape) | L |
| PND-9 | P2 | Backend de-duplication & dead code | (a) hub-router factory; (b) generic KB helpers; (c) remove dead `indian_law_kb.py` or wire it (FEA-12); (d) delete `gemini_service.py.rej` | M |
| PND-10 | P2 | Tests | (a) live-provider smoke tests behind a flag; (b) frontend component tests for new UI; (c) split slow backend suite | M |
| PND-11 | P3 | Reach (from roadmap) | (i18n moved to UXI-13, now P1) · PWA · encrypted object storage · pagination · Razorpay · lawyer referral · Capacitor mobile | XL |
