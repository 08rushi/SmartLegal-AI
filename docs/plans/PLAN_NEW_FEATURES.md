# New Features Plan (from 2026-11 R&D)

Principles: information not advice; cite real sources only; never invent statute sections; every feature works by voice and icon, not just text.

| ID | Pri | Feature | Sub-tasks | Depends | Effort |
|---|---|---|---|---|---|
| FEA-1 | High | Voice-first mode (speak question, hear answer, hi/mr/en) | (a) mic button + browser speech-to-text; (b) read-aloud on summary/clauses via speech synthesis; (c) language auto-pick; (d) fallback when unsupported; (e) later: BHASHINI API for more languages | UXI-1 | M |
| FEA-2 | High | "What should I do next?" card | (a) add `next_steps` (3 items) to analysis JSON, backward compatible; (b) prompt + Pydantic update; (c) `types/index.ts`; (d) card UI with audio | — | S |
| FEA-3 | High | Free legal aid finder | (a) static data: NALSA 15100, Tele-Law, State Legal Services Authority; (b) eligibility questions (Section 12); (c) page + links; (d) confirm current terms before launch | — | S |
| FEA-4 | High | Document generator: rental agreement, legal notice, RTI, consumer complaint | (a) template schema; (b) question-flow UI with live preview; (c) generate PDF; (d) disclaimer + lawyer-review note; (e) per-template tests; (f) verify any e-stamp claim before offering it | UXI-3 | L |
| FEA-5 | Med | Red-flag / "don't sign yet" alerts | (a) rules for hidden fees, auto-renewal, one-sided termination; (b) banner on analysis; (c) tests | — | S |
| FEA-6 | Med | Reminders & obligation tracker with nudges | (a) persisted reminders (PND-5); (b) extract deadlines from `your_obligations`; (c) WhatsApp/email nudge; (d) opt-out | PND-5 | M |
| FEA-7 | Med | Share summary via expiring link | (a) mount share router; (b) token + expiry + revoke; (c) read-only view; (d) ownership tests | PND-5 | M |
| FEA-8 | Med | Court fee & case-status helper (E-Courts links) | (a) fee table per state; (b) calculator UI; (c) deep links | — | M |
| FEA-9 | Med | Scan-paper camera upload | (a) camera capture; (b) auto-crop and multi-page; (c) feed OCR waterfall | — | M |
| FEA-10 | Low | DigiLocker import | (a) apply for requester access; (b) consent flow; (c) fetch docs | external approval | L |
| FEA-11 | Low | Lawyer referral / paid review | (a) lawyer directory; (b) booking; (c) payments | PND-11 | XL |
| FEA-12 | Med | Deterministic law citations | Wire real law KB into prompts; show source link per citation | PND-9 | M |
