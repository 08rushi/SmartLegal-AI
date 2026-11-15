# Master Task List (consolidated)

Details live in the four plan files. Mark `[~]` before starting, `[x]` only after tests pass.

## Parked (set aside by user on 2026-11-15; revisit later)
- [ ] BLK-5 Verify Gemini live (needs funded key)
- [ ] BLK-6 / PND-3 Google OAuth end-to-end check

## P0 — Blockers
- [ ] BLK-1 CI branch triggers
- [ ] BLK-2 Unify schema (Alembic as single source)
- [ ] BLK-3 Password-reset email
- [ ] BLK-4 Remove fake/placeholder UI

## P1 — Pending and high-value
- [ ] UXI-13 App-wide language switcher on Home (Marathi / Hindi / English) — whole app changes language
- [ ] BLK-7 WhatsApp sandbox · [ ] BLK-8 Production config
- [ ] PND-1 Real compare · [ ] PND-2 Tracker status · [ ] PND-6 Performance/DB · [ ] PND-7 Security tests
- [ ] FEA-1 Voice mode · [ ] FEA-2 Next-steps card · [ ] FEA-3 Legal aid finder · [ ] FEA-4 Document generator
- [ ] UXI-2 Simple home · [ ] UXI-3 Guided flow · [ ] UXI-4 Verdict-first analysis · [ ] UXI-5 Simple view

## P2 — Next
- [ ] PND-5 Persist/remove stubs · [ ] PND-8 Frontend dedupe · [ ] PND-9 Backend dedupe · [ ] PND-10 Tests
- [ ] FEA-5 Red flags · [ ] FEA-6 Reminders · [ ] FEA-7 Share link · [ ] FEA-8 Court fee · [ ] FEA-9 Camera scan · [ ] FEA-12 Law citations
- [ ] UXI-6 to UXI-11

## P3 — Later
- [ ] PND-11 i18n/PWA/storage/payments/mobile · [ ] FEA-10 DigiLocker · [ ] FEA-11 Lawyer referral · [ ] UXI-12 Visual refresh

## Milestones (revised 2026-11-15)
| Milestone | Tasks |
|---|---|
| M1 Foundation | BLK-1 CI · BLK-2 schema · BLK-3 reset email · BLK-4 remove fake UI |
| M2 Trust + language base | PND-7 security review · BLK-8 prod config · UXI-13a i18n framework + Home switcher + locale files · UXI-13b translate shell, Home, auth pages |
| M3 Compare and tracker | PND-1 · PND-2 · PND-6 |
| M4 Simple UI | UXI-13c translate all remaining pages and analysis content (Marathi field) · UXI-2 · UXI-4/5 · FEA-2 |
| M5–M8 | as before (new services, document generator, persistence, reach) |

## Docs
- [x] DOC-1 Plans created (this folder)
- [x] DOC-2 Status doc, CLAUDE.md and feature backlog pointed at these plans
- [ ] DOC-3 Reconcile old root trackers (`implementation_plan.md`, `phase*_plan.md`, `SMARTLEGAL_AI_AGENT_TASK_TRACKER.md`) with the code

## Status update 2026-11-15 (after M1-M4)
Done: BLK-1 CI triggers, BLK-2 schema parity (Alembic 0006 applied to Supabase), BLK-3 Resend reset email (needs RESEND_API_KEY/EMAIL_FROM), BLK-4 fake UI removed, BLK-8 production config checks, PND-7 security audit and fixes (#1-#12 except noted), UXI-13 app-wide Marathi/Hindi/English, voice input/output (FEA-1), verdict-first Analysis (FEA-2/UXI-4), status selector saves (PND-2, Legal ID).
Still open: BLK-5 Gemini live check and BLK-6 Google OAuth (parked), BLK-7 WhatsApp sandbox, PND-1 real compare, static hub/Yojana content translation (script written, not run), deployment (Render + Vercel, see docs/STAGING_DEPLOYMENT_CHECKLIST.md), native-speaker review of mr/hi text, rotate the Vercel recovery codes committed in git history (vercel-recovery-codes.txt).
