# SmartLegal AI — Document Analysis Failure Fix

## Root causes found in the supplied source and test documents

1. **Clause-response shape mismatch.** `backend/services/groq_service.py` requested a bare JSON array and rejected every parsed object. A provider/model response such as `{ "clauses": [...] }` therefore failed with `Unexpected response shape: dict`, even when the response contained usable clauses.
2. **Groq cooldown had no effective Gemini fallback.** The active analysis path used Groq and optionally OpenRouter, while the configured Gemini key was not used for text-analysis fallback. The legacy Gemini helper also referenced retired model IDs and the `google-generativeai` SDK, which is not in `backend/requirements.txt`.
3. **Gemini vision model was unset by default.** The supplied configuration had a Gemini API key but no `GEMINI_VISION_MODEL`. Scanned PDFs were eligible for the vision path based on the key, but the vision adapter then rejected the missing model configuration.
4. **Large/page-split scanned PDFs could continue with unreadable text.** The ARQ worker's page-splitting branch did not fail clearly when OCR was unavailable or OCR output remained unreadable. This could send near-empty text to legal analysis and end in `Analysis produced no valid clauses.`
5. **Redis could mask the terminal analysis state.** The status route checked Redis before the database. A stale Redis `processing` entry could hide a database `error` or completed result, causing the UI to poll repeatedly. The POST route also trusted cached `processing` without checking the database row.
6. **Deduplication could reuse a dead local temp-file path.** Upload hashing returned an existing record even when its `local://` file had disappeared. Re-analysis then failed before the model was called.
7. **Polling was too aggressive for slow OCR/model work.** The UI queried status every three seconds for up to five minutes. Polling now backs off to 15 seconds and has a 10-minute ceiling; terminal status is resolved from the database first so stale cache entries no longer keep the loop alive.

## Changes made

- Normalize common model wrappers (`clauses`, `items`, `results`, `extracted_clauses`, nested `data`/`analysis`) and single-clause objects into the expected list. Reject genuinely unusable output with a specific error.
- Treat malformed response-shape errors as retryable chunk errors.
- Add a direct HTTPX-based Gemini text fallback for Groq cooldown/API failure, using `GEMINI_VISION_MODEL` or the current registry default `gemini-3.8-flash`; OpenRouter remains the first fallback when configured.
- Set the default Gemini vision model to `gemini-3.8-flash` and send the Google API key in a header rather than a URL query parameter.
- Make both the API worker path and ARQ worker fail explicitly if page-split OCR is unavailable or unreadable, and prevent unreadable extracted text from reaching legal analysis.
- Make the database authoritative for terminal status in `GET /analyze/{document_id}/status`, and prevent stale cached `processing` from overriding terminal database state on `POST /analyze`.
- If a deduplicated upload points to a missing local temp file, restore the file and update the existing record rather than returning a dead path.
- Add `backend/tests/test_analysis_regressions.py` for clause-shape and retry-classification regressions.
- Back off frontend status polling (3s → gradually up to 15s; 10-minute ceiling).

## Validation performed

- Python syntax validation passed for the edited backend modules and regression test.
- Clause-response regression checks passed (7/7) using the installed runtime with a stub for the missing Groq package.
- PDF extraction/readability inspection was run against the supplied test PDFs. The four synthetic contract/court fixtures and text PDFs extracted readable text. `df426bb80fd6872ea086ae8d2fd99203.pdf` and `6 (1).pdf` are image-only/scanned PDFs and require OCR.
- Frontend TypeScript check passed (`node ./node_modules/typescript/bin/tsc --noEmit`).
- Frontend tests passed (20/20).
- Full backend pytest suite could not run in this environment because required packages (including `slowapi` and `groq`) are absent and package installation is blocked by unavailable network access. The user's local environment should run the backend tests after installing `backend/requirements.txt`.
- A live model/API run was not possible in this isolated environment. The fix provides the correct routing and parsing paths, but model output quality and provider quota still depend on valid API credentials, active model access, and available quota. No system can guarantee perfect legal analysis for every document; low-quality scans and uncertain legal interpretations must remain explicit rather than fabricated.

## Apply / verify on the development machine

1. Back up the current project and merge the modified files from this archive.
2. Confirm `GROQ_API_KEY` and `GEMINI_API_KEY` are valid in `backend/.env`.
3. Keep `CLOUD_VISION_ENABLED=true` and `PRIVACY_MODE=false` only if cloud OCR is permitted. If using local OCR, install Tesseract and set `TESSERACT_CMD` if it is not on PATH.
4. Restart both the FastAPI server and the ARQ worker (if Redis-backed jobs are enabled). Restarting only FastAPI does not update a separately running worker process.
5. Re-upload any document whose old `local://` path has expired. The upload route now restores missing local files on hash matches.
6. Run `cd backend && python -m pytest -q`; run `cd frontend && npm test` and `npm run build` on the Windows development machine.
7. Test the four `*_Test.pdf` fixtures first, then the scanned PDFs. Scanned PDFs should either be OCR-transcribed or return a clear OCR-specific error—not an empty-clause error.
