# SmartLegal-AI Release Checklist

Run this checklist before every release. Do not ship if any critical item fails.

## Core Release Gate

- [ ] Upload works
  - Valid PDF uploads successfully.
  - Upload progress reaches completion.
  - File preview works.
  - Invalid/oversized/mismatched files are rejected cleanly.

- [ ] Analyze works
  - Uploaded PDF starts analysis.
  - Polling reaches `done`.
  - Analysis page renders summary and clauses.
  - `/analysis/:documentId` works after refresh.
  - Failed analysis can be retried with forced re-analysis.

- [ ] Chat works
  - Chat opens for the current document.
  - User question sends successfully.
  - Assistant answer returns and renders.
  - Both user and assistant messages persist after refresh.
  - Chat history loads for the active document.
  - Chat does not show stale messages from another document.

- [ ] Auth works
  - Register works.
  - Login works.
  - Refresh restores session from `sl_token`.
  - Logout clears session.
  - Invalid token is handled safely.

- [ ] Ownership secure
  - User A cannot access User B documents.
  - User A cannot analyze User B documents.
  - User A cannot poll User B analysis status.
  - User A cannot delete User B analysis cache.
  - User A cannot chat with User B documents.
  - User A cannot fetch User B chat history.

- [ ] PDFs parse
  - Text-based PDF extracts non-empty text.
  - Corrupt PDF fails with safe error.
  - Scanned/textless PDF fails with safe error or supported OCR path.
  - Image upload behavior matches actual backend capability.
  - UI copy matches PDF-only upload support unless OCR/image support is implemented.

- [ ] AI schema valid
  - Analysis result includes `summary`.
  - Analysis result includes `clauses`.
  - Clauses include required fields.
  - Summary includes required fields and risk counts.
  - Old cached analysis JSON still renders.
  - Malformed AI output does not crash the app.

- [ ] Hindi/English output valid
  - `plain_english` is present.
  - `plain_hindi` is present.
  - Clause language toggle works.
  - Hindi text renders correctly.
  - Legal-language changes are reviewed for accuracy.

- [ ] My Documents works
  - Logged-in user sees own uploaded documents.
  - Refresh keeps history available.
  - Opening a previous document recovers analysis or starts analysis safely.
  - Other users' documents are not shown.

- [ ] Life services hubs work
  - `/legal-id`, `/property-hub`, and `/business-hub` load public guidance cards.
  - Each detail page loads services, FAQs, legal protections, and official links.
  - Logged-in users can create Legal ID, Property, and Business application trackers.
  - Checklists load and save for each service application type.
  - User A cannot access or update User B service applications/checklists.

- [ ] Service Tracker works
  - `/tracker` requires login and shows a clear sign-in state when logged out.
  - Logged-in users see Legal ID, Property, and Business applications in one list.
  - Tracker counts active, completed, and reminder items correctly.
  - Reminder date and note persist after refresh in the same browser.
  - Notification permission flow handles granted, denied, and unsupported browsers cleanly.

- [ ] No placeholder routes exposed
  - `/compare` is either production-ready or clearly hidden/renamed.
  - Google Sign-In is hidden unless backend route is mounted and verified.
  - UI does not expose unimplemented payments, WhatsApp, life-services, voice, PWA queue, or lawyer referral flows.
  - Buttons do not lead to dead or misleading screens.

## Documentation Gate

- [ ] `MASTER_CONTEXT.md` reflects release reality.
- [ ] `CURRENT_STATE_DIFF.md` reflects new changes.
- [ ] `PROJECT_RULES_OF_ENGAGEMENT.md` still matches protected contracts.
- [ ] `TESTING_PROTOCOL.md` is updated if test scope changed.
- [ ] README/env docs mention current AI provider and env vars.

## Final Decision

Release status:
- [ ] PASS - safe to release.
- [ ] FAIL - do not release; fix blockers first.

Release notes owner:
- Name:
- Date:
- Version/commit:
- Known limitations:

