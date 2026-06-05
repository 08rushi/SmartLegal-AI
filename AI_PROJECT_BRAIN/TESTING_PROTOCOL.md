# SmartLegal-AI Testing Protocol

Purpose: prevent future upgrades from silently breaking SmartLegal-AI.

Live code is the source of truth. These tests should be run manually today and automated over time with backend API tests, frontend component tests, and end-to-end browser tests.

## Test Data

Maintain a small local fixture set:
- Valid text-based rental agreement PDF.
- Valid text-based employment contract PDF.
- Valid text-based loan agreement PDF.
- Scanned/image-only PDF.
- Corrupt PDF with `.pdf` extension.
- JPEG/PNG/WebP sample.
- Renamed file mismatch, e.g. PNG content named `fake.pdf`.
- Oversized file above 10 MB.

Never commit real user legal documents.

## 1. Upload Tests

Goal: ensure file selection, validation, storage, Redux state, and navigation keep working.

Manual/API cases:
- Upload valid text PDF under 10 MB.
- Confirm backend returns `201` with `document.id`, `filename`, `file_url`, `file_size`, `status = "ready"`.
- Confirm frontend stores `document.current`.
- Confirm upload progress reaches 100.
- Confirm file preview appears before upload.
- Confirm successful upload triggers analysis.
- Confirm successful analysis navigates to `/analysis/:documentId`.
- Upload with no auth token and confirm current anonymous policy.
- Upload while logged in and confirm document `user_id` belongs to the logged-in user.

Negative cases:
- Upload empty file, expect `400`.
- Upload over 10 MB, expect `400`.
- Upload unsupported file type, expect `400`.
- Upload renamed/mismatched extension, expect `400`.
- Simulate Cloudinary failure and confirm local temp fallback still works.

Regression checks:
- Upload UI must not claim unsupported file types work.
- Frontend accepted file types must match backend analysis capability.

## 2. Auth Tests

Goal: ensure account creation, login, token persistence, and logout work.

Cases:
- Register new user with valid name/email/password.
- Duplicate email registration returns clean error.
- Login with valid credentials returns user and access token.
- Login with wrong password returns `401`.
- `/auth/me` works with valid Bearer token.
- `/auth/me` fails with invalid/expired token.
- Refresh frontend page after login and confirm session restores.
- Logout clears Redux auth state and removes `sl_token`.

Google auth cases:
- If Google route is mounted, Google Sign-In returns platform JWT.
- If Google route is not mounted, frontend must not present it as working.
- Verify Google token audience before accepting credential.

## 3. Ownership Tests

Goal: ensure users cannot access each other's documents, analyses, cache, or chat.

Setup:
- Create User A.
- Create User B.
- User A uploads and analyzes Document A.
- User B uploads and analyzes Document B.

Required cases:
- User A can fetch Document A.
- User B cannot fetch Document A.
- User B cannot start analysis for Document A.
- User B cannot poll status for Document A.
- User B cannot delete cache for Document A.
- User B cannot chat against Document A.
- User B cannot fetch chat history for Document A.
- User A cannot access Document B.

Expected responses:
- Missing token: `401` where auth is required.
- Wrong owner: consistent `403` or `404`.
- Document owner: normal `200`.

Anonymous policy tests:
- Define whether anonymous docs are public demo docs, same-session docs, or disabled.
- Test and document the chosen behavior explicitly.

## 4. Analysis Polling Tests

Goal: ensure asynchronous analysis contract remains stable.

Cases:
- POST `/analyze` on new document returns `{ status: "processing", document_id }` or cached `{ analysis }`.
- Frontend polls `/analyze/{documentId}/status` every 3 seconds.

## 5. Life Services and Tracker Tests

Goal: ensure Legal ID, Property, Business License, and 4D tracker flows remain usable and ownership-safe.

Public guidance cases:
- Open `/services` and confirm Legal ID, Property, Business License, and Service Tracker cards are visible.
- Open `/legal-id`, `/property-hub`, and `/business-hub`; confirm guidance cards load from backend public endpoints.
- Open one detail page from each hub and confirm services, FAQs, legal protections, disclaimers, and official links render.

Authenticated tracker cases:
- Login as User A.
- Create one application from Legal ID, one from Property, and one from Business.
- Confirm each application appears on its source hub detail page.
- Open each checklist, toggle at least one item, save, refresh, and confirm the saved state remains.
- Open `/tracker` and confirm all three applications appear in one list with correct statuses and counts.
- Set a reminder date and note on `/tracker`, refresh, and confirm the reminder persists in the same browser.
- Enable browser notifications where supported and confirm due reminders produce a notification while the app is open.

Ownership cases:
- Login as User B.
- Confirm User B cannot list, fetch, update, delete, or save checklist items for User A service applications.
- Expected responses: missing token `401`; wrong owner consistent `403` or `404`.
- Status eventually returns `{ status: "done", analysis }`.
- Analysis result contains `document_id` and `analyzed_at`.
- UI shows skeleton while processing.
- UI renders result after completion.
- Failed analysis returns clean error state.
- Retry Analysis sends `force_reanalyze = true` and bypasses stale failed SQLite rows.
- Polling timeout shows user-safe message.

Edge cases:
- Poll status before background task writes processing row.
- Poll invalid document ID.
- AI provider failure.
- Empty text extraction.
- Server restart during background task.

Contract rule:
- Do not change this API shape without updating `analysisSlice.ts` and docs.

## 5. Cache Tests

Goal: ensure Redis/SQLite cache behavior is correct and safe.

Cases:
- First analysis of a document calls AI and writes SQLite analysis row.
- Second analysis returns SQLite cached result when Redis is disabled.
- With Redis enabled, first completed analysis writes Redis.
- With Redis enabled, next analysis returns Redis result.
- SQLite hit backfills Redis.
- `force_reanalyze = true` clears Redis and SQLite stale result before starting new analysis.
- Error results are not cached in Redis.
- Cache delete endpoint removes Redis and SQLite result.

Security cases:
- Wrong user cannot clear another user's cache.
- Wrong user cannot read another user's cached analysis.

Regression checks:
- Cached old JSON payloads still render in frontend.
- Adding new AI fields does not break old cached results.

## 6. Chat Isolation Tests

Goal: ensure chat only uses the active user's active document and does not leak across documents.

Cases:
- Open Chat after analyzing Document A; chat uses Document A.
- Send question; user message appears immediately.
- Assistant response appears and is stored.
- Switch to Document B; old Document A chat must not appear as current chat unless intentionally loaded by document.
- Refresh page and verify stored chat history loads for the active document.
- User A cannot chat against User B's document.
- User A cannot fetch User B's chat history.

Backend persistence cases:
- Store both user and assistant messages.
- Fetch history ordered by timestamp.
- Chat history must be scoped by `document_id` and owner.

AI cases:
- Chat answer includes disclaimer.
- Chat answer remains document-grounded.
- Chat rejects/handles questions when document text cannot be extracted.

## 7. PDF Validation Tests

Goal: ensure only analyzable files enter the analysis pipeline.

Cases:
- Valid text PDF opens with PyMuPDF and extracts non-empty text.
- Scanned/image-only PDF returns clear "could not extract text" message.
- Corrupt PDF fails gracefully.
- PDF with renamed extension mismatch is rejected at upload.
- Non-PDF image upload is either rejected before analysis or processed through a real OCR/image path.
- Empty PDF or textless PDF does not create misleading zero-risk analysis.

Backend validation checks:
- Magic bytes are checked.
- File size is checked.
- Extension/content mismatch is checked.
- PDF parse check should happen before expensive AI call.

Roadmap rule:
- Do not claim image support until OCR/image analysis tests pass.

## 8. AI JSON Schema Tests

Goal: prevent model output drift from breaking UI or storing malformed results.

Minimum clause schema:
- `id`
- `title`
- `original_text`
- `plain_english`
- `plain_hindi`
- `risk_level`
- `risk_score`
- `risk_reason`
- `clause_type`

Minimum summary schema:
- `document_type`
- `parties`
- `key_dates`
- `overall_risk`
- `risk_summary`
- `total_clauses`
- `high_risk_count`
- `medium_risk_count`
- `low_risk_count`

Cases:
- AI returns valid JSON object.
- AI returns fenced JSON; cleanup succeeds.
- AI returns malformed JSON; failure is handled without crashing app.
- One chunk fails JSON parse; remaining chunks still produce result.
- All chunks fail; fallback result is valid and frontend renders it.
- Risk level is only `low`, `medium`, or `high`.
- Risk score matches risk level range.
- `plain_hindi` is present.
- `plain_english` is present.
- Summary counts match actual clause risk levels.

Future schema cases:
- `law_references` can be added without breaking old UI.
- `negotiation_suggestions` can be added without breaking old UI.
- `signing_scenarios` can be added without breaking old UI.

Rule:
- Store only validated analysis JSON.

## 9. Regression Tests For Roadmap-Critical Flows

These flows must stay green before adding Phase 2-5 features.

Core MVP:
- Register -> refresh -> still logged in.
- Login -> upload PDF -> analyze -> view `/analysis/:documentId`.
- Refresh `/analysis/:documentId` -> document and analysis recover.
- Ask chat question about current document.
- Open My Documents -> see uploaded document.
- Logout -> protected/private data no longer accessible.

Phase 2 AI expansion:
- Rental agreement detects rental type.
- Employment contract detects employment type.
- Loan agreement detects loan type.
- Analysis includes Hindi and English.
- Risk reasons cite Indian law carefully.
- Bad AI JSON does not break app.

Phase 3 accessibility:
- Existing upload/analyze/chat flow remains keyboard-usable.
- Hindi text still renders.
- Offline banner does not block page.
- Future Simple Mode must not remove Expert Mode data.

Phase 4 life-services:
- Guidance flows must not access uploaded legal documents unless explicitly needed.
- Official-source links must be displayed for government processes.
- Platform fee must be clearly separate from government fee.

Phase 5 bots/payments:
- Billing tier checks must not bypass document ownership.
- WhatsApp document upload must create owner-scoped documents.
- AI Lawyer Bot must reuse legal safety rules and disclaimers.

## Automation Roadmap

Recommended automation order:
1. Backend pytest API tests for auth/upload/ownership.
2. Backend tests for analysis cache and schema validation using mocked AI.
3. Frontend unit tests for Redux slices.
4. Playwright end-to-end tests for upload -> analyze -> chat.
5. Fixture-based AI prompt regression tests.
6. Security regression tests for cross-user access.

## Release Gate

Before merging roadmap upgrades, verify:
- Upload flow passes.
- Auth flow passes.
- Ownership isolation passes.
- Analysis polling passes.
- Cache behavior passes.
- Chat isolation passes.
- PDF validation passes.
- AI schema tests pass.
- Critical regression flow passes.

## Mandatory Pre-Release Checklist

Before every release, confirm all of the following are true:
- Upload works.
- Analyze works.
- Chat works.
- Auth works.
- Ownership is secure.
- PDFs parse.
- AI schema is valid.
- Hindi and English output are valid.
- My Documents works.
- No placeholder routes are exposed.

Release rule:
- If any item above fails, do not release.
- If a feature is intentionally unavailable, hide or disable its route/UI before release.
- If ownership is not secure, release is blocked regardless of other feature status.
