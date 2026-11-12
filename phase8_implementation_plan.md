# SmartLegal-AI — Phase 8 Implementation Plan v1.1
## Frontend Confidence & Error UX

**Document ID**: `SL-PLAN-PHASE8-V1.1`  
**Status**: `READY FOR FINAL REVIEW — IMPLEMENTATION NOT AUTHORIZED`  
**Date**: `2026-09-24`  
**Frozen Dependencies**: Phases 1 through 7 (Frozen)  
**Target Scope**: Frontend Confidence, Readability Provenance, `[UNCLEAR]` Handling, State Machine, Partial-Failure Alerts & Error UX  

---

## Revision History

| Version | Date | Author | Summary of Changes |
|---|---|---|---|
| `v1.0` | 2026-09-24 | Core AI Team | Initial architectural audit and implementation plan. |
| `v1.1` | 2026-09-24 | Core AI Team | **Mandatory Corrections Pass**: <br>1. Removed elapsed-time stage simulation; introduced default Indeterminate Processing state.<br>2. Added dedicated 7-state Frontend Analysis State Machine.<br>3. Enforced strict tripartite separation (OCR confidence vs. Readability quality vs. Legal accuracy).<br>4. Preserved null/unknown semantics (never coerce null to 0%).<br>5. Preserved `[UNCLEAR]` uncertainty semantics (not legal error/falsehood).<br>6. Added Phase 7 isolation acceptance criteria (CER/WER forbidden in UI).<br>7. Added Phase 6 telemetry filtering (strip internal scratch paths/parameters).<br>8. Added user-triggered advocate escalation rule (no automated modal popups).<br>9. Translated partial-analysis implementation jargon to citizen-facing language.<br>10. Formalized WCAG 2.1 AA accessibility (no reliance on color/icon/hover alone).<br>11. Added responsive/mobile requirements across desktop, tablet, and mobile.<br>12. Added strict backend-change gate ("Requires explicit authorization").<br>13. Reaffirmed Phase 8 boundary (no Phase 9 canary/shadow, no legal accuracy scoring).<br>14. Updated acceptance criteria to encompass all corrections. |

---

## A. Executive Summary & Problem Statement

Phase 8 introduces **Frontend Confidence & Error UX** to the SmartLegal-AI platform.

Over Phases 1 through 6, the document ingestion and processing backend was hardened with rich telemetry:
- **Phase 2**: Per-page typographic quality scoring (`quality_score`), native digital vs. scanned classification (`page_type`), and triage indicators (`is_unclear`).
- **Phase 3**: Token-aware chunking with graceful partial-failure preservation (`is_partial`, `completion_ratio`, `incomplete_chunks`).
- **Phase 4**: Visual/OCR waterfall with engine provenance, fallback history, and explicit `[UNCLEAR]` degradation markers.
- **Phase 5**: Provider budget management with rate-limit cooloff, queued error classification, and automatic OpenRouter failover.
- **Phase 6**: Adaptive document optimization with compression telemetry (`optimization_applied`, `compression_ratio`, `optimization_method`, `page_split`).
- **Phase 7**: Production-independent Accuracy Evaluation Framework (strictly isolated offline benchmarks).

### The Frontend Gap:
The existing frontend (`frontend/src/`) currently treats document analysis as a binary operation: it either displays all clauses or shows a generic full-page error. Crucial backend signals are either completely ignored or rendered as raw unformatted strings:
1. `metadata` from the backend response is completely discarded by Redux (`analysisSlice.ts`).
2. When partial chunks fail (e.g. 6 of 7 chunks succeed, 1 fails due to rate limits), the frontend fails entirely or ignores the missing pages.
3. Raw `[UNCLEAR]` markers emitted by the OCR pipeline appear as literal unformatted text in clauses.
4. Document legibility provenance (digital vector vs. OCR scan) is invisible to the user.
5. Optimization savings from Phase 6 are never surfaced.
6. Long processing states render a static skeleton without informative feedback.

### Core Architectural Principles for Phase 8:
1. **Strict Legal Non-Equivalence**: Technical legibility and OCR confidence must **never** be equated with legal validity or attorney approval.
2. **Preserve Truthful Semantics**: Missing confidence remains "Not available" (never coerced to 0%). `[UNCLEAR]` signifies obscured physical text, not legal invalidity.
3. **No Fabricated Stages**: Never simulate stage progression using arbitrary timers. Use indeterminate processing unless authoritative stages are exposed.
4. **User-Triggered Escalation**: Human advocate escalation is strictly user-initiated; modals never pop up automatically.
5. **Multi-Channel Accessibility**: Uncertainty and status warnings must never rely solely on color, icons, or hover states.

---

## B. Current Frontend Architecture Audit

### 1. Component & State Inventory

| File / Component | Existing Role | Audit Findings & Phase 8 Deficiencies |
|---|---|---|
| [`frontend/src/types/index.ts`](file:///c:/Core/SmartLegal-AI/frontend/src/types/index.ts) | Core TypeScript interfaces | `AnalysisResult` only defines `document_id`, `summary`, `clauses`, and `analyzed_at`. Completely omits `metadata`. `DocumentSummary` omits `is_partial`. |
| [`frontend/src/store/analysisSlice.ts`](file:///c:/Core/SmartLegal-AI/frontend/src/store/analysisSlice.ts) | Redux state for analysis | Polls `GET /analyze/{id}/status` every 3s. Discards metadata; only stores `action.payload` directly into `state.result`. Any failure throws and wipes out any partial clauses. |
| [`frontend/src/pages/Upload.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/pages/Upload.tsx) | Upload & preview cockpit | Validates 25 MB limit client-side. If analysis fails, renders raw error string in a generic red box at the bottom. No optimization feedback. |
| [`frontend/src/pages/Analysis.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/pages/Analysis.tsx) | Analysis results cockpit | Shows `AnalysisSkeleton` during loading. Does not display partial-failure alerts, legibility chips, or document optimization badges. |
| [`frontend/src/components/ClauseCard.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/components/ClauseCard.tsx) | Clause accordion card | Renders `original_text` as raw monospace. If `[UNCLEAR]` is present, it appears as raw literal text without explanation, tooltips, or caution banners. |
| [`frontend/src/components/analysis/AnalysisProcessingProgress.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/components/analysis/AnalysisProcessingProgress.tsx) | Stage progress indicator | **Orphaned Component**. Defines stages (`queued`, `extracting`, `ocr`, `analyzing`, `completed`, `failed`) and progress bar, but is not rendered in any page. |
| [`frontend/src/components/analysis/AnalysisRiskSummaryCard.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/components/analysis/AnalysisRiskSummaryCard.tsx) | Summary header card | Displays executive summary, high-risk points, obligations, parties, and dates. Has no slot for document legibility or partial analysis warnings. |
| [`frontend/src/components/ui/LegalDisclaimerBanner.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/components/ui/LegalDisclaimerBanner.tsx) | Regulatory disclaimer | Correctly cites the Advocates Act, 1961. Ready for persistent integration. |
| [`frontend/src/components/ui/LawyerEscalationModal.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/components/ui/LawyerEscalationModal.tsx) | Advocate escalation | Exists and functions; ready to be linked directly from `[UNCLEAR]` and partial failure callouts. |

---

## C. Existing Backend Result Contracts (Audit Verification)

### 1. `GET /analyze/{document_id}/status` Contract
Inspection of `backend/routers/analyze.py` (lines 482–539) reveals the exact contract returned by the polling endpoint:

```python
# In backend/routers/analyze.py:
# 1. In progress:
return {"status": "processing"}

# 2. Server/worker error:
return {"status": "error", "error": message}

# 3. Completed:
return {"status": "done", "analysis": result}
```

**Key Architectural Finding**:
The backend status endpoint returns **ONLY** `status: "processing" | "done" | "error"`. It does **NOT** expose intermediate granular stages (`stage: "extracting"`, `progress_pct: 45%`, etc.) to the client.

### 2. Analysis Payload Structure (`analysis`)
When `status === "done"`, `analysis` contains:
```json
{
  "document_id": "doc_123456",
  "analyzed_at": "2026-09-24T04:00:00.000Z",
  "status": "done",
  "summary": {
    "document_type": "Commercial Lease Agreement",
    "language": "English",
    "overall_risk": "high",
    "risk_summary": "Document contains unilateral termination clauses...",
    "total_clauses": 14,
    "high_risk_count": 3,
    "medium_risk_count": 5,
    "low_risk_count": 6,
    "is_partial": false
  },
  "clauses": [
    {
      "id": "clause_1",
      "title": "Security Deposit Forfeiture",
      "original_text": "The Lessor may forfeit the deposit if [UNCLEAR] occurs within 30 days.",
      "plain_english": "The landlord can keep your deposit if an unspecified condition occurs.",
      "plain_hindi": "यदि 30 दिनों के भीतर कोई अस्पष्ट स्थिति उत्पन्न होती है तो मकान मालिक आपकी जमा राशि जब्त कर सकता है।",
      "risk_level": "high",
      "risk_score": 8,
      "risk_reason": "Unclear condition creates open-ended landlord discretion.",
      "clause_type": "Security Deposit",
      "page_number": 2,
      "chunk_index": 0
    }
  ],
  "metadata": {
    "pipeline_version": "v1.0.0",
    "prompt_version": "2026-03-v2",
    "model": "llama-3.3-70b-versatile",
    "analyzed_at": "2026-09-24T04:00:00.000Z",
    "completion_ratio": 0.8571,
    "total_chunks": 7,
    "successful_chunks": 6,
    "incomplete_chunks": [
      {
        "chunk_id": "chunk_7",
        "chunk_index": 6,
        "page_start": 12,
        "page_end": 14,
        "error_type": "rate_limit",
        "error_message": "Rate limit exceeded"
      }
    ],
    "optimization": {
      "original_size_bytes": 24890123,
      "optimized_size_bytes": 7120340,
      "optimization_applied": true,
      "optimization_method": "lossless",
      "pages_optimized": 14,
      "pages_split": 0,
      "technical_quality_score": 0.94,
      "compression_ratio": 0.286
    }
  }
}
```

---

## D. Removal of Simulated Stages & Strict Backend-Change Gate

### 1. Mandatory Stage Simulation Removal
- **Prohibition**: The frontend must **NEVER** simulate processing stages using elapsed timers (e.g. treating $0\text{--}30\text{s}$ as "extracting", $30\text{--}60\text{s}$ as "OCR", and $60\text{s}+$ as "analyzing").
- **Rationale**: Simulating stages deceives the user into believing the system is in a specific phase when it may actually be queued in ARQ or waiting on provider rate-limit cooloff.
- **Default Frontend Behavior**:
  - The frontend will display an **Indeterminate Processing State**.
  - The UI will present an animated pulsing indicator or indeterminate progress bar with clear, factual messaging:
    ```
    "Analyzing Document... Securely reading text and evaluating clauses against Indian statutory codes."
    ```
  - An elapsed time counter (`"Processing for 42s..."`) may be displayed for user reassurance, but without fabricated phase claims.
  - A cancel/back button allows the user to abort polling safely.

### 2. Strict Backend-Change Gate
If authoritative stage tracking is required in the future:
> [!CAUTION]
> **BACKEND CONTRACT MODIFICATION GATE**:
> Updating `GET /analyze/{id}/status` to return authoritative job stages (e.g. `{"status": "processing", "stage": "extracting", "progress_pct": 35}`) requires modifying backend code (`routers/analyze.py` and `worker.py`).
> **This requires separate, explicit user authorization.**
> Under Phase 8 authorization, NO backend code shall be modified. The frontend will strictly operate on existing backend contracts via the Indeterminate Processing state.

---

## E. Frontend Analysis State Machine

The frontend Redux slice and UI components will derive the UI state deterministically from existing backend API responses.

```
                           ┌────────────────────────┐
                           │      Initial Idle      │
                           └───────────┬────────────┘
                                       │ User submits document
                                       ▼
                           ┌────────────────────────┐
                           │         queued         │
                           └───────────┬────────────┘
                                       │ POST /analyze returns 202
                                       ▼
                           ┌────────────────────────┐
       ┌───────────────────┤       processing       ├────────────────────┐
       │                   └───────────┬────────────┘                    │
       │ Poll error:                   │ Poll success:                   │ Poll error:
       │ Provider cooloff / 429        │ status == "done"                │ Hard failure / timeout
       ▼                               ▼                                 ▼
┌─────────────────────────┐            │                     ┌────────────────────────┐
│  provider_unavailable   │            │                     │         failed         │
│        / queued         │            │                     └────────────────────────┘
└─────────────────────────┘            │
                                       ├─────────────────────────────────┐
                       is_partial == false                               │ is_partial == true OR
                       completion_ratio >= 1.0                           │ completion_ratio < 1.0
                       incomplete_chunks == []                           │ incomplete_chunks != []
                                       │                                 │
                     ┌─────────────────┴─────────────────┐               │
                     │                                   │               │
            No [UNCLEAR] in text              Has [UNCLEAR] in text      │
                     │                                   │               │
                     ▼                                   ▼               ▼
          ┌─────────────────────┐             ┌─────────────────────┐ ┌─────────────────────┐
          │      completed      │             │   completed_with_   │ │       partial       │
          │                     │             │     uncertainty     │ │                     │
          └─────────────────────┘             └─────────────────────┘ └─────────────────────┘
```

### State Derivation Definitions

| Frontend State | Derivation Rule from Existing Backend Contracts | UI Presentation | Primary User Actions |
|---|---|---|---|
| `queued` | `POST /analyze` returns `{ status: "processing" }` or poll cycle 0 before first worker response. | "Job received — queued for analysis worker..." | Cancel / Navigate away |
| `processing` | `GET /analyze/{id}/status` returns `{ status: "processing" }`. | Indeterminate progress bar + elapsed timer: "Analyzing document against Indian statutory codes..." | Cancel polling |
| `completed` | `status === "done" && !summary.is_partial && (metadata?.completion_ratio ?? 1.0) >= 1.0 && (!metadata?.incomplete_chunks \|\| metadata.incomplete_chunks.length === 0)` AND no clause contains `[UNCLEAR]`. | Full analysis cockpit with all clauses, executive summary, and "High Readability" legibility badge. | Export PDF, Ask Q&A, Save |
| `completed_with_uncertainty` | `status === "done" && !summary.is_partial && (metadata?.completion_ratio ?? 1.0) >= 1.0` BUT one or more clauses contain `[UNCLEAR]`. | Full analysis view, but clauses with `[UNCLEAR]` render `UnclearTextPill` badges and an uncertainty caution banner. | View original text, Ask Advocate (user click) |
| `partial` | `status === "done" && (summary.is_partial === true \|\| (metadata?.completion_ratio !== null && metadata.completion_ratio < 1.0) \|\| (metadata?.incomplete_chunks && metadata.incomplete_chunks.length > 0))`. | Renders non-blocking `PartialAnalysisAlert` banner above tabs, lists unanalyzed page ranges, qualifies risk as "Preliminary Risk". | Re-analyze Missing Pages, Ask Advocate |
| `failed` | `status === "error"` where the error message is NOT a provider cooloff/queue error, or polling times out. | Categorized error alert card explaining cause (e.g. unreadable scan, corrupted PDF, file $>25$ MB). | Re-upload cleaner scan, Compress PDF |
| `provider_unavailable / queued` | `POST /analyze` returns 429 OR `status === "error"` with error text containing `"cooloff"`, `"rate-limited"`, `"Retry after"`, or `ProviderQueuedError` / `ProviderUnavailableError`. | Informational banner: "AI Provider Capacity Reached. Server is handling peak volume. Automatic retry in progress." | Retry Now button with countdown |

---

## F. Strict Separation: OCR Confidence vs. Readability vs. Legal Accuracy

To protect citizens and comply with the Advocates Act, 1961, the frontend must strictly enforce a tripartite separation of concepts:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   TRIPARTITE SEPARATION                                │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│ 1. OCR Confidence        │ 2. Technical Readability    │ 3. Legal Accuracy             │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ Statistical probability  │ Typographic density and     │ Semantic validity, statutory  │
│ (0.0 to 1.0) of pixel-to-│ coherence heuristic         │ compliance, and contractual   │
│ glyph optical recognition│ (letter-to-symbol ratio)    │ enforceability under law      │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ Source: Tesseract /      │ Source: Phase 2             │ Source: Qualified Advocate    │
│ PaddleOCR / Gemini Vision│ `quality_score`             │ registered with Bar Council   │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ Label: "OCR Legibility"  │ Label: "Document Readability│ **NEVER COMPUTED BY AI**      │
│ or "Scan Legibility"     │ or "Extraction Quality"     │ Protected by Advocates Act    │
└──────────────────────────┴─────────────────────────────┴───────────────────────────────┘
```

### Strict Prohibition Rules:
1. The frontend must **NEVER** label OCR confidence or typographic quality as:
   - `"Legal Accuracy"`
   - `"Document Accuracy"`
   - `"Contract Accuracy"`
   - `"Accuracy: 95%"`
   - or any equivalent phrase implying legal verification.
2. The UI must label technical metrics strictly as **"Document Legibility"** or **"Text Readability"**.
3. Every analysis screen must persistently render the [`LegalDisclaimerBanner`](file:///c:/Core/SmartLegal-AI/frontend/src/components/ui/LegalDisclaimerBanner.tsx) affirming that AI analysis does not constitute formal legal representation.

---

## G. Preservation of Null / Unknown Semantics

In real-world legal document processing, confidence cannot always be computed:
- Native digital PDFs have vector text layers; OCR is not run, so `ocr_confidence` is genuinely `None`/`null`.
- Certain OCR engines (or fallback paths) may not return a calibrated scalar.

### Rules for Frontend Rendering:
1. **Never Coerce Null to 0%**:
   - `null` or `undefined` must **NEVER** be displayed as `0%`. Displaying `0%` falsely tells the user that the document is completely illegible or failed.
2. **Explicit Null Representation**:
   - For native digital documents: Display `"Not applicable (Digital document)"` or omit the OCR metric entirely while displaying the `"Native Digital Text"` badge.
   - For scanned documents where OCR confidence is missing: Display `"Legibility: Not available"` or `"Readability: Standard"`.
3. **No Fabricated Scores**: The UI must never invent a default score (like 80% or 100%) when the backend returns `null`.

---

## H. Preservation of `[UNCLEAR]` Semantics

The Phase 4 OCR pipeline emits `[UNCLEAR]` when source text is physically illegible (due to ink smudges, tears, folds, stamps, low resolution, or watermarks).

### Rules for Frontend Interpretation:
1. **Uncertainty Marker Only**:
   - `[UNCLEAR]` represents **unreadable source text**.
   - It must **NOT** be interpreted as:
     - Confirmed incorrect text
     - Legal error or violation
     - False or fraudulent information
     - Low legal accuracy
2. **UI Implementation (`UnclearTextPill`)**:
   - In `ClauseCard.tsx`, any occurrence of `[UNCLEAR]` in `original_text` or `plain_english` will be replaced with an inline styled component:
     ```tsx
     <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-500/15 border border-amber-400/30 text-amber-300 font-mono text-xs font-semibold" title="Portions of this clause were unreadable in the source document scan.">
       <span aria-hidden="true">⚠️</span>
       <span>[Unclear in Source]</span>
     </span>
     ```
3. **Clause-Level Physical Verification Caution**:
   - When a clause contains `[UNCLEAR]`, the expanded clause card displays:
     ```
     ⚠️ Legibility Notice: Portions of this clause were obscured in the uploaded scan. Verify the original physical document before signing or acting.
     ```

---

## I. Phase 6 Telemetry Filtering (Information Disclosure)

Only citizen-relevant optimization telemetry may be rendered in the UI.

### 1. Allowed User-Facing Optimization Fields:
- `original_size_bytes` & `optimized_size_bytes` (formatted as MB/KB, e.g. "24.8 MB → 7.1 MB").
- `compression_ratio` (formatted as percentage reduction, e.g. "71% smaller").
- `optimization_applied` (`true` / `false`).
- `optimization_method` (translated to user-friendly terms: `"Lossless Optimization"`, `"Image Downsampling"`, or `"Multi-Page Segmentation"`).
- `pages_optimized` and `pages_split`.

### 2. Strictly Prohibited Internal Fields:
The frontend must **NEVER** expose:
- Local filesystem paths or scratch directory paths (e.g. `C:\Core\...`, `/tmp/...`, `scratch/opt_...`).
- Internal DPI settings, quantization tables, or Ghostscript parameters.
- Raw Pillow / PyMuPDF flags.
- Internal provider worker timings or Redis keys.

---

## J. User-Triggered Advocate Escalation Rule

Connecting a citizen with a verified advocate under the Advocates Act, 1961 is a critical legal interaction.

### Escalation Interaction Rules:
1. **Strictly User-Triggered**:
   - The [`LawyerEscalationModal`](file:///c:/Core/SmartLegal-AI/frontend/src/components/ui/LawyerEscalationModal.tsx) must open **ONLY** when the user explicitly clicks an "Ask Advocate" or "Connect with Advocate" button.
2. **Prohibition on Automated Popups**:
   - The modal must **NEVER** open automatically based on:
     - Low OCR confidence
     - Low quality score
     - Presence of `[UNCLEAR]` tokens
     - Partial analysis state
     - Failed chunks
   - Intrusive popups create false panic and degrade user trust.
3. **Contextual Pre-fill**:
   - When the user clicks "Ask Advocate" from a partial analysis banner or an unclear clause, the modal opens with the document name and specific clause concern pre-populated in the note field for convenience.

---

## K. Partial-Analysis UX & Terminology Translation

When `is_partial === true` or `completion_ratio < 1.0`, the system must explain the situation constructively without exposing developer jargon.

### Terminology Translation Matrix:

| Backend Implementation Field / Value | Developer Jargon (PROHIBITED IN UI) | Citizen-Facing Language (MANDATORY IN UI) |
|---|---|---|
| `incomplete_chunks[i]` | "Chunk 3 execution failed" | "Pages 8–10 were not analyzed" |
| `completion_ratio: 0.857` | "completion_ratio = 0.857142" | "86% Document Analyzed" |
| `total_chunks: 7, successful: 6` | "6/7 chunks succeeded" | "6 of 7 document sections analyzed" |
| `error_type: "rate_limit"` | "HTTP 429 TPM Rate Limit Exceeded" | "Temporary server capacity limit" |
| `error_type: "transient"` | "Connection timeout / 504 Gateway" | "Temporary network interruption" |
| `summary.is_partial: true` | "Partial chunk failure" | "Partial Document Analysis" |
| `summary.overall_risk` | "Overall Risk: High" | "Preliminary Risk: High (based on 86% of document)" |

### `PartialAnalysisAlert` Component Specification:
- Rendered above the tab navigation in [`pages/Analysis.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/pages/Analysis.tsx).
- Displays:
  - Header: `"Partial Document Analysis (86% Complete)"`
  - Body: `"Pages 12–14 could not be analyzed due to temporary server load. The analyzed clauses from the rest of your document are displayed below."`
  - Action 1: `"🔄 Re-analyze Missing Pages"` (re-triggers `/analyze` with `force_reanalyze: true`).
  - Action 2: `"⚖️ Ask Advocate"` (opens escalation modal on click).

---

## L. Accessibility Requirements (WCAG 2.1 AA)

All status, confidence, and uncertainty indicators must adhere to WCAG 2.1 AA accessibility standards:

### 1. Multi-Channel Perception:
- **No Reliance on Color Alone**:
  - High risk: Red background + ⚠️ icon + visible text label `"High Risk"`.
  - Partial analysis: Amber background + ⚠️ icon + visible text label `"Partial Analysis"`.
  - Successful legibility: Emerald background + ✓ icon + visible text label `"High Readability"`.
- **No Reliance on Icons Alone**:
  - Every icon is paired with visible text or an explicit `aria-label`.
- **No Reliance on Hover Alone**:
  - Information in tooltips must be accessible via keyboard focus (`tabIndex={0}`, `aria-describedby`) or click/touch disclosure toggles, never solely on CSS `:hover`.

### 2. Screen Reader Semantics:
- `PartialAnalysisAlert`: `role="alert"` with `aria-live="polite"`.
- Indeterminate Progress: `role="status"` with `aria-label="Analyzing document"`.
- Clause Cards: Accordion headers use standard `<button aria-expanded={expanded} aria-controls={contentId}>`.

### 3. Contrast Ratios:
- All text on dark glassmorphic panels (`#0b1120`, `#121a2d`) must exceed $4.5:1$ contrast:
  - Amber text: `#fde68a` on `#2a2410` (contrast ratio $\approx 6.4:1$).
  - Rose text: `#fecdd3` on `#2a1320` (contrast ratio $\approx 6.1:1$).
  - Slate text: `#cbd5e1` on `#121a2d` (contrast ratio $\approx 8.2:1$).

---

## M. Responsive & Mobile Requirements

The new components must adapt seamlessly across desktop, tablet, and mobile form factors:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        RESPONSIVE ADAPTATION                           │
├─────────────────┬───────────────────┬──────────────────────────────────┤
│ Breakpoint      │ Viewport Width    │ Layout Behavior                  │
├─────────────────┼───────────────────┼──────────────────────────────────┤
│ Desktop         │ >= 1280px         │ Dual-column cockpit; full badges;│
│                 │                   │ inline re-analyze / advocate CTA │
├─────────────────┼───────────────────┼──────────────────────────────────┤
│ Tablet          │ 768px - 1024px    │ Single-column wrap; action       │
│                 │                   │ buttons wrap to secondary row    │
├─────────────────┼───────────────────┼──────────────────────────────────┤
│ Mobile          │ < 768px           │ Full-width vertical stack; touch │
│                 │ (360px - 414px)   │ targets >= 44x44px; bottom sheet │
│                 │                   │ escalation modal; no overflow    │
└─────────────────┴───────────────────┴──────────────────────────────────┘
```

- **Touch Targets**: All interactive pills, retry buttons, and modal dismiss triggers must have a minimum touch target size of $44 \times 44\text{ px}$.
- **Horizontal Overflow Prevention**: Long file names, clause titles, and failed page tags must use `break-words` and `truncate` to prevent horizontal scrolling on mobile viewports.

---

## N. Phase 7 Isolation & Non-Exposure

Phase 7 developed the offline Accuracy Evaluation Framework. Its metrics are strictly internal engineering benchmarks.

### Strict Isolation Rules:
1. The production frontend must **NEVER** import from `backend/evaluation/`.
2. The production frontend must **NEVER** display:
   - CER (Character Error Rate)
   - WER (Word Error Rate)
   - SequenceMatcher similarity metrics
   - Confusion matrices or TP/FP/FN counts
   - UNCLEAR F1 scores
   - OCR/CER correlation coefficients
   - Phase 7 benchmark test results
3. **Acceptance Gate**: An automated check will verify that no Phase 7 evaluation metric names appear in the frontend bundle.

---

## O. Security & Privacy Constraints

1. **Stack Trace Sanitization**: Server traceback strings (`Traceback (most recent call last)...`, file paths) must be intercepted by client error boundaries and sanitized to user-friendly messages before DOM rendering.
2. **Secret / Key Hygiene**: Provider names, API keys, and internal Redis/DB connection strings must never appear in error cards or telemetry chips.
3. **Local Privacy Mode**: When the backend indicates privacy mode (`settings.privacy_mode === true`), the UI displays:
   `"🔒 Local Processing: Document was analyzed locally without external cloud vision."`

---

## P. Proposed TypeScript Data Contracts

### [`frontend/src/types/index.ts`](file:///c:/Core/SmartLegal-AI/frontend/src/types/index.ts) Additions

```typescript
// ─── Phase 8: Analysis Telemetry & Confidence Contracts ──────────────────────

export interface IncompleteChunkInfo {
  chunk_id: string
  chunk_index: number
  page_start: number
  page_end: number
  error_type?: string
  error_message?: string
}

export interface OptimizationTelemetryInfo {
  original_size_bytes: number
  optimized_size_bytes: number
  optimization_applied: boolean
  optimization_method: 'lossless' | 'image_stream' | 'downsample' | 'page_split' | 'none'
  pages_optimized: number
  pages_split: number
  optimization_reason?: string
  technical_quality_score?: number
  compression_ratio?: number
}

export interface AnalysisMetadata {
  pipeline_version?: string
  prompt_version?: string
  model?: string
  analyzed_at?: string
  completion_ratio?: number
  total_chunks?: number
  successful_chunks?: number
  incomplete_chunks?: IncompleteChunkInfo[]
  optimization?: OptimizationTelemetryInfo
}

// ─── Extended Existing Contracts ─────────────────────────────────────────────

export interface DocumentSummary {
  document_type: string
  language?: string
  parties: string[]
  key_dates: { label: string; date: string }[]
  overall_risk: RiskLevel
  risk_summary: string
  total_clauses: number
  high_risk_count: number
  medium_risk_count: number
  low_risk_count: number
  high_risk_clauses?: string[]
  beneficial_clauses?: string[]
  your_obligations?: string[]
  other_party_rights?: string[]
  // Phase 8 Addition:
  is_partial?: boolean
}

export interface AnalysisResult {
  document_id: string
  summary: DocumentSummary
  clauses: Clause[]
  analyzed_at: string
  // Phase 8 Addition:
  metadata?: AnalysisMetadata
}
```

---

## Q. Component Architecture & Redux Changes

### 1. New Components (under `frontend/src/components/analysis/`):
- **`UnclearTextPill.tsx`**: Renders `[Unclear in Source]` with warning icon, keyboard-accessible tooltip, and physical verification advice.
- **`PartialAnalysisAlert.tsx`**: Non-blocking banner rendered above analysis tabs when `completion_ratio < 1.0` or `is_partial === true`. Displays unanalyzed page ranges and actions.
- **`OptimizationBadge.tsx`**: Surfaces compression savings (`24.8 MB → 7.1 MB, 71% smaller`) without internal technical parameters.
- **`DocumentReadabilityBadge.tsx`**: Displays `"Native Digital Text"` vs. `"OCR Scan"` legibility provenance.

### 2. Modified Components:
- **`ClauseCard.tsx`**: Tokenizes `original_text` and `plain_english` to embed `UnclearTextPill`; adds legibility caution box when `[UNCLEAR]` is present; displays OCR scan tag.
- **`pages/Analysis.tsx`**: Integrates Indeterminate Processing state during `isLoading`; conditionally renders `PartialAnalysisAlert`, `OptimizationBadge`, and `DocumentReadabilityBadge`.
- **`pages/Upload.tsx`**: Displays optimization notice for files $> 8$ MB; renders structured error card with actionable retry buttons.
- **`store/analysisSlice.ts`**: Preserves `metadata` and `is_partial`; exports `retryMissingChunks({ documentId })`.

---

## R. Sub-Phases (8A – 8J) Execution Roadmap

When authorized, implementation will proceed sequentially:

- **8A**: TypeScript Types & Data Contract Extension (`types/index.ts`).
- **8B**: Redux Slice Alignment & Metadata Preservation (`store/analysisSlice.ts`).
- **8C**: `UnclearTextPill` & Clause Text Parser Component (`components/analysis/UnclearTextPill.tsx`).
- **8D**: `ClauseCard` Uncertainty Callout & Page Provenance Badge (`components/ClauseCard.tsx`).
- **8E**: `PartialAnalysisAlert` Banner Component (`components/analysis/PartialAnalysisAlert.tsx`).
- **8F**: `OptimizationBadge` & `DocumentReadabilityBadge` Components.
- **8G**: Integration into `pages/Analysis.tsx` (Indeterminate Processing, Alerts, Badges).
- **8H**: Integration into `pages/Upload.tsx` (Pre-analysis sizing & Error alerts).
- **8I**: Responsive Layout & WCAG 2.1 AA Accessibility Audit.
- **8J**: Automated Frontend Tests & Clean Production Build Verification.

---

## S. Updated Acceptance Criteria

1. **No Simulated Stages**: The frontend does not simulate processing stages based on arbitrary elapsed timers. Uses an Indeterminate Processing state.
2. **Strict Backend-Change Gate**: No backend files are modified under Phase 8. Any backend change request is gated and marked "Requires explicit authorization".
3. **State Machine Conformance**: All 7 frontend states (`queued`, `processing`, `completed`, `completed_with_uncertainty`, `partial`, `failed`, `provider_unavailable / queued`) derive deterministically from existing contracts.
4. **Tripartite Separation**: OCR confidence and technical readability are never labeled as "Legal Accuracy", "Document Accuracy", or "Contract Accuracy".
5. **Null Preservation**: `null` or `undefined` OCR confidence is displayed as "Not applicable" or "Not available", and is never coerced to `0%`.
6. **Uncertainty Semantics**: `[UNCLEAR]` is treated solely as an unreadable text marker; it is never branded as a legal error, invalid clause, or false information.
7. **Phase 7 Isolation**: No Phase 7 benchmark metrics (CER, WER, SequenceMatcher, confusion matrices) appear in frontend code or user interface.
8. **Phase 6 Telemetry Filtering**: No scratch paths, DPI parameters, or internal optimizer flags reach the UI. Only citizen-relevant savings are shown.
9. **User-Triggered Escalation**: The `LawyerEscalationModal` is triggered solely by explicit user click. No automated popup on uncertainty or failure.
10. **Partial Analysis UX**: Implementation terms like "chunk failure" are translated to user-facing terms like "Pages 12–14 were not analyzed".
11. **WCAG 2.1 AA Accessibility**: Status and uncertainty indicators do not rely solely on color, icons, or hover states. Minimum contrast $\ge 4.5:1$ met.
12. **Responsive Layout**: All components adapt cleanly across desktop, tablet, and mobile viewports with touch targets $\ge 44 \times 44\text{ px}$.
13. **Phase 8 Boundary**: No Phase 9 functionality (shadow mode, canary routing, A/B testing) is implemented.
14. **Clean Production Build**: `npm run build` (`tsc && vite build`) succeeds with 0 errors.

---

## T. Risk Register

| Risk | Impact | Probability | Mitigation Strategy |
|---|---|---|---|
| User confuses OCR legibility with legal accuracy | High | Medium | Explicit labels ("Document Legibility", NOT "Legal Accuracy"); persistent Advocates Act disclaimer on every page. |
| Missing chunks cause user panic | Medium | Low | Frame partial failure constructively: "85% analyzed; unread pages are highlighted; retry available". |
| `[UNCLEAR]` token regex breaks custom clause formatting | Low | Low | Parse plain string replacement into React elements using robust AST tokenization. |
| User overwhelmed by technical optimization numbers | Low | Low | Display simplified savings ("71% smaller") and hide technical byte calculations in accessible tooltips. |

---

## U. Final Authorization Gate

```
================================================================================
PHASE 8 PLAN v1.1:
READY FOR FINAL REVIEW — IMPLEMENTATION NOT AUTHORIZED
================================================================================
```
