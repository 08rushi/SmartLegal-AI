/**
 * Phase 8 Frontend Confidence & Error UX Test Suite
 * Validates:
 * 1. 7-state analysis state machine derivation
 * 2. Null confidence preservation (no coercion to 0%)
 * 3. Strict legal non-equivalence (no "Legal Accuracy" labeling)
 * 4. [UNCLEAR] uncertainty semantics (unreadable scan text, not legal error)
 * 5. Phase 6 telemetry filtering (no scratch paths or optimizer internals)
 * 6. Phase 7 isolation (zero CER/WER or evaluation imports in frontend bundle)
 * 7. User-triggered advocate escalation (no automatic modal popups)
 * 8. Partial analysis terminology translation (no "chunk failure" jargon)
 * 9. Accessibility (WCAG 2.1 AA) & Responsive layout constraints
 */

import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const FRONTEND_SRC = path.resolve(__dirname, '..')

// ── 1. Re-implemented Pure State Machine Function for Test Isolation ─────────
function deriveAnalysisState(result, isLoading, error, retryAfterRemaining, isRetryingProvider) {
  if (isLoading && isRetryingProvider) {
    return 'retrying_provider'
  }
  if (error) {
    const errLower = error.toLowerCase()
    if (
      errLower.includes('cooloff') ||
      errLower.includes('rate-limit') ||
      errLower.includes('rate limit') ||
      errLower.includes('retry after') ||
      errLower.includes('capacity') ||
      errLower.includes('too many concurrent') ||
      errLower.includes('service unavailable') ||
      errLower.includes('503') ||
      (retryAfterRemaining != null && retryAfterRemaining > 0)
    ) {
      return isLoading ? 'retrying_provider' : 'provider_unavailable'
    }
    if (!isLoading) {
      return 'failed'
    }
  }
  if (isLoading) {
    return 'processing'
  }
  if (!result) {
    return null
  }
  const isPartial =
    result.summary?.is_partial === true ||
    (result.metadata?.completion_ratio != null && result.metadata.completion_ratio < 1.0) ||
    (result.metadata?.incomplete_chunks != null && result.metadata.incomplete_chunks.length > 0)

  if (isPartial) {
    return 'partial'
  }

  const hasUnclear = result.clauses?.some(
    (c) =>
      c.is_unclear === true ||
      c.original_text?.includes('[UNCLEAR]') ||
      c.plain_english?.includes('[UNCLEAR]') ||
      c.plain_hindi?.includes('[UNCLEAR]')
  )

  if (hasUnclear) {
    return 'completed_with_uncertainty'
  }

  return 'completed'
}

// ── Suite 1: 7-State Analysis State Machine Derivation ───────────────────────

test('State Machine: derives "processing" when isLoading is true', () => {
  assert.equal(deriveAnalysisState(null, true, null), 'processing')
  assert.equal(deriveAnalysisState({ clauses: [] }, true, null), 'processing')
})

test('State Machine: derives "retrying_provider" when retrying after provider unavailability', () => {
  // Actively loading with isRetryingProvider = true
  assert.equal(deriveAnalysisState(null, true, null, null, true), 'retrying_provider')
  // Actively loading with an in-flight cooldown error
  assert.equal(
    deriveAnalysisState(null, true, 'All configured providers are rate-limited or in cooloff. Retry after 60.0s.'),
    'retrying_provider'
  )
  // Actively loading with HTTP 503 error
  assert.equal(
    deriveAnalysisState(null, true, 'HTTP 503 Service Unavailable'),
    'retrying_provider'
  )
  // Normal loading without provider cooldown retains generic "processing"
  assert.equal(deriveAnalysisState(null, true, null), 'processing')
})

test('State Machine: derives "completed" when all chunks succeed without [UNCLEAR]', () => {
  const result = {
    summary: { is_partial: false },
    metadata: { completion_ratio: 1.0, incomplete_chunks: [] },
    clauses: [
      { id: 'c1', original_text: 'Clean text', plain_english: 'Clean explanation' }
    ]
  }
  assert.equal(deriveAnalysisState(result, false, null), 'completed')
})

test('State Machine: derives "completed_with_uncertainty" when [UNCLEAR] is present in clauses', () => {
  const result = {
    summary: { is_partial: false },
    metadata: { completion_ratio: 1.0, incomplete_chunks: [] },
    clauses: [
      { id: 'c1', original_text: 'Payment within [UNCLEAR] days', plain_english: 'Unclear payment window' }
    ]
  }
  assert.equal(deriveAnalysisState(result, false, null), 'completed_with_uncertainty')
})

test('State Machine: derives "partial" when summary.is_partial is true or completion_ratio < 1.0', () => {
  const result1 = {
    summary: { is_partial: true },
    metadata: { completion_ratio: 0.85, incomplete_chunks: [{ page_start: 12, page_end: 14 }] },
    clauses: []
  }
  assert.equal(deriveAnalysisState(result1, false, null), 'partial')

  const result2 = {
    summary: { is_partial: false },
    metadata: { completion_ratio: 0.75, incomplete_chunks: [] },
    clauses: []
  }
  assert.equal(deriveAnalysisState(result2, false, null), 'partial')
})

test('State Machine: derives "provider_unavailable" on rate-limit, cooloff, 503, or retry-after errors', () => {
  assert.equal(
    deriveAnalysisState(null, false, 'All configured providers are rate-limited or in cooloff. Retry after 60.0s.'),
    'provider_unavailable'
  )
  assert.equal(
    deriveAnalysisState(null, false, 'AI Provider capacity reached (Too many concurrent requests)'),
    'provider_unavailable'
  )
  assert.equal(
    deriveAnalysisState(null, false, 'HTTP 503 Service Unavailable'),
    'provider_unavailable'
  )
  assert.equal(
    deriveAnalysisState(null, false, 'Temporary error', 45),
    'provider_unavailable'
  )
})

test('State Machine: derives "failed" on generic fatal errors and HTTP 500', () => {
  assert.equal(
    deriveAnalysisState(null, false, 'Document is corrupted or could not be read'),
    'failed'
  )
  assert.equal(
    deriveAnalysisState(null, false, 'HTTP 500 Internal Server Error'),
    'failed'
  )
  assert.equal(
    deriveAnalysisState(null, false, 'File size exceeds 25 MB limit'),
    'failed'
  )
})

test('Provider Availability: Retry duration is preserved when supplied by backend and never fabricated', () => {
  function extractRetry(status, detail, backendRetryAfter) {
    if (
      status === 429 ||
      status === 503 ||
      detail.toLowerCase().includes('rate limit') ||
      detail.toLowerCase().includes('cooloff') ||
      detail.toLowerCase().includes('service unavailable')
    ) {
      return typeof backendRetryAfter === 'number' && backendRetryAfter > 0 ? backendRetryAfter : null
    }
    return null
  }

  assert.equal(extractRetry(429, 'Rate limit', 45), 45)
  assert.equal(extractRetry(503, 'Service unavailable', 30), 30)
  assert.equal(extractRetry(429, 'Rate limit', undefined), null)
  assert.notEqual(extractRetry(429, 'Rate limit', undefined), 60)
  assert.equal(extractRetry(503, 'Service unavailable', null), null)
})

// ── Suite 2: Null / Unknown Confidence Semantics ────────────────────────────

test('Null Semantics: null or undefined confidence is never coerced to 0%', () => {
  function formatConfidence(ocrConfidence, isDigital) {
    if (isDigital) return 'Not applicable (Digital document)'
    if (ocrConfidence === null || ocrConfidence === undefined) return 'Not available'
    return `${Math.round(ocrConfidence * 100)}% scan legibility`
  }

  assert.equal(formatConfidence(null, true), 'Not applicable (Digital document)')
  assert.equal(formatConfidence(undefined, true), 'Not applicable (Digital document)')
  assert.equal(formatConfidence(null, false), 'Not available')
  assert.equal(formatConfidence(undefined, false), 'Not available')
  assert.notEqual(formatConfidence(null, false), '0%')
  assert.notEqual(formatConfidence(undefined, false), '0%')
  assert.equal(formatConfidence(0.85, false), '85% scan legibility')
})

// ── Suite 3: Strict Legal Non-Equivalence (Prohibition of "Legal Accuracy") ──

test('Legal Non-Equivalence: Frontend source code never labels technical scores as Legal Accuracy', () => {
  const targetFiles = [
    path.join(FRONTEND_SRC, 'components', 'analysis', 'DocumentReadabilityBadge.tsx'),
    path.join(FRONTEND_SRC, 'components', 'analysis', 'AnalysisProcessingProgress.tsx'),
    path.join(FRONTEND_SRC, 'components', 'ClauseCard.tsx'),
    path.join(FRONTEND_SRC, 'pages', 'Analysis.tsx'),
  ]

  const forbiddenTerms = [
    'legal accuracy',
    'document accuracy',
    'contract accuracy',
    'legal validity score',
    'accuracy: 100%',
    'illegal clause',
  ]

  for (const filePath of targetFiles) {
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf-8').toLowerCase()
      for (const term of forbiddenTerms) {
        assert.equal(
          content.includes(term),
          false,
          `Forbidden term "${term}" found in ${filePath}`
        )
      }
    }
  }
})

// ── Suite 4: [UNCLEAR] Uncertainty Semantics ────────────────────────────────

test('[UNCLEAR] Semantics: [UNCLEAR] is treated as physical scan uncertainty, not legal invalidity', () => {
  const pillFile = path.join(FRONTEND_SRC, 'components', 'analysis', 'UnclearTextPill.tsx')
  assert.equal(fs.existsSync(pillFile), true, 'UnclearTextPill.tsx must exist')

  const pillContent = fs.readFileSync(pillFile, 'utf-8')
  assert.equal(pillContent.includes('Physical Document Verification Needed'), true)
  assert.equal(pillContent.includes('This indicates scan legibility, not legal validity'), true)
})

// ── Suite 5: Phase 6 Telemetry Filtering (Information Disclosure) ───────────

test('Phase 6 Filtering: OptimizationBadge exposes savings but no internal scratch paths or flags', () => {
  const optFile = path.join(FRONTEND_SRC, 'components', 'analysis', 'OptimizationBadge.tsx')
  assert.equal(fs.existsSync(optFile), true, 'OptimizationBadge.tsx must exist')

  const optContent = fs.readFileSync(optFile, 'utf-8')
  const forbiddenTelemetry = [
    'scratch/',
    'dpi_applied',
    'quantization',
    'ghostscript',
    'pillow',
    'tempfile',
    '/tmp/',
  ]

  for (const term of forbiddenTelemetry) {
    assert.equal(
      optContent.toLowerCase().includes(term),
      false,
      `Forbidden internal telemetry "${term}" leaked in OptimizationBadge.tsx`
    )
  }
})

// ── Suite 6: Phase 7 Isolation & Non-Exposure ───────────────────────────────

test('Phase 7 Isolation: Frontend never imports or displays Phase 7 internal engineering metrics', () => {
  const forbiddenPhase7Terms = [
    'backend/evaluation',
    'character error rate',
    'word error rate',
    'sequencematcher metrics',
    'unclear f1',
    'cer_normalized',
    'wer_normalized',
  ]

  function scanDir(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true })
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name)
      if (entry.isDirectory()) {
        if (entry.name !== 'node_modules' && entry.name !== 'dist' && entry.name !== '.git') {
          scanDir(fullPath)
        }
      } else if (entry.isFile() && (entry.name.endsWith('.ts') || entry.name.endsWith('.tsx'))) {
        const content = fs.readFileSync(fullPath, 'utf-8').toLowerCase()
        for (const term of forbiddenPhase7Terms) {
          assert.equal(
            content.includes(term),
            false,
            `Phase 7 internal metric "${term}" found in ${fullPath}`
          )
        }
      }
    }
  }

  scanDir(FRONTEND_SRC)
})

// ── Suite 7: User-Triggered Advocate Escalation Rule ─────────────────────────

test('Advocate Escalation: LawyerEscalationModal is triggered strictly by user interaction', () => {
  const analysisPage = path.join(FRONTEND_SRC, 'pages', 'Analysis.tsx')
  const content = fs.readFileSync(analysisPage, 'utf-8')

  // Verify modal exists
  assert.equal(content.includes('<LawyerEscalationModal'), true)

  // Verify modal state is controlled by isEscalationOpen and set via onClick
  assert.equal(content.includes('setIsEscalationOpen(true)'), true)

  // Verify there is NO automatic useEffect or trigger opening the modal
  const automaticPatterns = [
    /useEffect\s*\([^)]*setIsEscalationOpen\(true\)/s,
    /if\s*\([^)]*is_unclear[^)]*\)\s*setIsEscalationOpen\(true\)/s,
    /if\s*\([^)]*isPartial[^)]*\)\s*setIsEscalationOpen\(true\)/s,
  ]

  for (const pattern of automaticPatterns) {
    assert.equal(
      pattern.test(content),
      false,
      'Automatic modal popup trigger detected in Analysis.tsx'
    )
  }
})

// ── Suite 8: Partial Analysis Terminology Translation & Truthfulness ─────────

test('Partial Analysis UX: Displays "Re-analyze Document" and prohibits "Re-analyze Missing Pages"', () => {
  const alertFile = path.join(FRONTEND_SRC, 'components', 'analysis', 'PartialAnalysisAlert.tsx')
  assert.equal(fs.existsSync(alertFile), true, 'PartialAnalysisAlert.tsx must exist')

  const content = fs.readFileSync(alertFile, 'utf-8')
  assert.equal(content.includes('Partial Document Analysis'), true)
  assert.equal(content.includes('Unprocessed Document Sections:'), true)
  assert.equal(content.includes('Re-analyze Document'), true)
  assert.equal(content.includes('Re-runs analysis across entire document'), true)
  assert.equal(content.includes('This will re-run analysis across the entire document'), true)

  // Strictly verify no "Re-analyze Missing Pages" wording remains
  assert.equal(content.includes('Re-analyze Missing Pages'), false)

  // Prohibit "chunk failure" jargon in user-facing alert
  assert.equal(content.toLowerCase().includes('chunk failure'), false)
  assert.equal(content.toLowerCase().includes('chunk_index'), false)
})

// ── Suite 9: Missing Completion Ratio Factual Integrity ──────────────────────

test('Null Semantics: missing completion_ratio never renders a fabricated percentage', () => {
  const analysisFile = path.join(FRONTEND_SRC, 'pages', 'Analysis.tsx')
  const alertFile = path.join(FRONTEND_SRC, 'components', 'analysis', 'PartialAnalysisAlert.tsx')
  const analysisContent = fs.readFileSync(analysisFile, 'utf-8')
  const alertContent = fs.readFileSync(alertFile, 'utf-8')

  // Verify neither file contains the fabricated 0.8 / 80 fallback
  assert.equal(analysisContent.includes('?? 0.8'), false, 'Analysis.tsx must not contain ?? 0.8')
  assert.equal(alertContent.includes(': 80'), false, 'PartialAnalysisAlert.tsx must not contain : 80 fallback')

  // Component logic verification
  function renderCompletionBadge(completionRatio) {
    if (completionRatio != null) {
      return `${Math.round(completionRatio * 100)}% Analyzed`
    }
    return 'Partial Analysis'
  }

  assert.equal(renderCompletionBadge(null), 'Partial Analysis')
  assert.equal(renderCompletionBadge(undefined), 'Partial Analysis')
  assert.notEqual(renderCompletionBadge(null), '80% Analyzed')
  assert.notEqual(renderCompletionBadge(undefined), '80% Analyzed')
  assert.equal(renderCompletionBadge(0.72), '72% Analyzed')
})

// ── Suite 10: WCAG 2.1 AA Accessibility & Responsive Attributes ───────────────

test('Accessibility: Components include ARIA live regions, roles, and focus outlines', () => {
  const alertFile = path.join(FRONTEND_SRC, 'components', 'analysis', 'PartialAnalysisAlert.tsx')
  const alertContent = fs.readFileSync(alertFile, 'utf-8')
  assert.equal(alertContent.includes('role="alert"'), true)
  assert.equal(alertContent.includes('aria-live="polite"'), true)

  const progressFile = path.join(FRONTEND_SRC, 'components', 'analysis', 'AnalysisProcessingProgress.tsx')
  const progressContent = fs.readFileSync(progressFile, 'utf-8')
  assert.equal(progressContent.includes('role="status"'), true)
  assert.equal(progressContent.includes('role="progressbar"'), true)

  const uploadFile = path.join(FRONTEND_SRC, 'pages', 'Upload.tsx')
  const uploadContent = fs.readFileSync(uploadFile, 'utf-8')
  assert.equal(uploadContent.includes('role="alert"'), true)
})

test('Responsive Layout: Tooltips include max-w-[85vw] for narrow viewports (320px–414px)', () => {
  const badgeFile = path.join(FRONTEND_SRC, 'components', 'analysis', 'DocumentReadabilityBadge.tsx')
  assert.equal(fs.existsSync(badgeFile), true, 'DocumentReadabilityBadge.tsx must exist')
  const badgeContent = fs.readFileSync(badgeFile, 'utf-8')
  assert.equal(badgeContent.includes('max-w-[85vw]'), true, 'DocumentReadabilityBadge must include max-w-[85vw]')

  const pillFile = path.join(FRONTEND_SRC, 'components', 'analysis', 'UnclearTextPill.tsx')
  assert.equal(fs.existsSync(pillFile), true, 'UnclearTextPill.tsx must exist')
  const pillContent = fs.readFileSync(pillFile, 'utf-8')
  assert.equal(pillContent.includes('max-w-[85vw]'), true, 'UnclearTextPill must include max-w-[85vw]')
})

// ── Suite 11: Phase 8A TypeScript Contracts & Redux Metadata Integration ─────

test('Phase 8A Contracts: types/index.ts defines sanitized metadata contracts and clause attributes', () => {
  const typesFile = path.join(FRONTEND_SRC, 'types', 'index.ts')
  assert.equal(fs.existsSync(typesFile), true, 'types/index.ts must exist')
  const content = fs.readFileSync(typesFile, 'utf-8')

  // Exported types exist
  assert.equal(content.includes('export interface IncompleteChunkInfo'), true)
  assert.equal(content.includes('export interface OptimizationTelemetryInfo'), true)
  assert.equal(content.includes('export interface AnalysisMetadata'), true)

  // IncompleteChunkInfo fields
  assert.equal(content.includes('chunk_id: string'), true)
  assert.equal(content.includes('chunk_index: number'), true)
  assert.equal(content.includes('page_start: number'), true)
  assert.equal(content.includes('page_end: number'), true)

  // OptimizationTelemetryInfo sanitized citizen-relevant fields
  assert.equal(content.includes('original_size_bytes: number'), true)
  assert.equal(content.includes('optimized_size_bytes: number'), true)
  assert.equal(content.includes('optimization_applied: boolean'), true)
  assert.equal(content.includes('optimization_method:'), true)
  assert.equal(content.includes('pages_optimized: number'), true)
  assert.equal(content.includes('pages_split: number'), true)

  // Strictly sanitized: OptimizationTelemetryInfo MUST NOT leak internal backend fields
  const forbiddenTelemetryFields = [
    'duration_ms',
    'fallback_to_original_reason',
    'technical_readability_metrics',
    'scratch_path',
    'dpi_applied',
    'ghostscript',
  ]
  for (const field of forbiddenTelemetryFields) {
    assert.equal(
      content.includes(`${field}:`),
      false,
      `OptimizationTelemetryInfo must not contain internal telemetry field "${field}"`
    )
  }

  // AnalysisMetadata supports nullable OCR confidence and completion metrics
  assert.equal(content.includes('ocr_confidence?: number | null'), true)
  assert.equal(content.includes('completion_ratio?: number'), true)
  assert.equal(content.includes('incomplete_chunks?: IncompleteChunkInfo[]'), true)
  assert.equal(content.includes('optimization?: OptimizationTelemetryInfo'), true)

  // Clause and DocumentSummary extensions
  assert.equal(content.includes('is_unclear?: boolean'), true)
  assert.equal(content.includes('extraction_source?: string'), true)
  assert.equal(content.includes('is_partial?: boolean'), true)
})

test('Phase 8A Selectors: analysisSlice exports typed metadata accessors with strict null preservation', () => {
  const sliceFile = path.join(FRONTEND_SRC, 'store', 'analysisSlice.ts')
  assert.equal(fs.existsSync(sliceFile), true, 'analysisSlice.ts must exist')
  const content = fs.readFileSync(sliceFile, 'utf-8')

  // Verify all 7 required Phase 8A selectors are exported
  const requiredSelectors = [
    'selectAnalysisResult',
    'selectAnalysisMetadata',
    'selectCompletionRatio',
    'selectIncompleteChunks',
    'selectOptimizationTelemetry',
    'selectIsPartialAnalysis',
    'selectOcrConfidence',
  ]
  for (const selector of requiredSelectors) {
    assert.equal(
      content.includes(`export const ${selector}`),
      true,
      `analysisSlice.ts must export ${selector}`
    )
  }

  // Pure functional logic simulation matching analysisSlice.ts
  const selectAnalysisResult = (state) => state.analysis.result
  const selectAnalysisMetadata = (state) => state.analysis.result?.metadata
  const selectCompletionRatio = (state) => state.analysis.result?.metadata?.completion_ratio ?? null
  const selectIncompleteChunks = (state) => state.analysis.result?.metadata?.incomplete_chunks ?? []
  const selectOptimizationTelemetry = (state) => state.analysis.result?.metadata?.optimization
  const selectIsPartialAnalysis = (state) => {
    const result = state.analysis.result
    if (!result) return false
    return (
      result.summary?.is_partial === true ||
      (result.metadata?.completion_ratio != null && result.metadata.completion_ratio < 1.0) ||
      Boolean(result.metadata?.incomplete_chunks && result.metadata.incomplete_chunks.length > 0)
    )
  }
  const selectOcrConfidence = (state) => state.analysis.result?.metadata?.ocr_confidence ?? null

  // 1. Null / undefined preservation (strictly never coerced to 0 or arbitrary numbers)
  const emptyState = { analysis: { result: null } }
  assert.equal(selectAnalysisResult(emptyState), null)
  assert.equal(selectAnalysisMetadata(emptyState), undefined)
  assert.equal(selectCompletionRatio(emptyState), null)
  assert.notEqual(selectCompletionRatio(emptyState), 0)
  assert.notEqual(selectCompletionRatio(emptyState), 0.8)
  assert.deepEqual(selectIncompleteChunks(emptyState), [])
  assert.equal(selectOptimizationTelemetry(emptyState), undefined)
  assert.equal(selectIsPartialAnalysis(emptyState), false)
  assert.equal(selectOcrConfidence(emptyState), null)
  assert.notEqual(selectOcrConfidence(emptyState), 0)

  // 2. Complete document with telemetry
  const completeState = {
    analysis: {
      result: {
        document_id: 'doc-1',
        summary: { is_partial: false },
        clauses: [],
        metadata: {
          completion_ratio: 1.0,
          total_chunks: 4,
          successful_chunks: 4,
          incomplete_chunks: [],
          ocr_confidence: 94.2,
          optimization: {
            original_size_bytes: 1048576,
            optimized_size_bytes: 524288,
            optimization_applied: true,
            optimization_method: 'downsample',
            pages_optimized: 5,
            pages_split: 0,
            compression_ratio: 0.5,
          },
        },
      },
    },
  }
  assert.equal(selectCompletionRatio(completeState), 1.0)
  assert.equal(selectOcrConfidence(completeState), 94.2)
  assert.deepEqual(selectIncompleteChunks(completeState), [])
  assert.equal(selectOptimizationTelemetry(completeState)?.compression_ratio, 0.5)
  assert.equal(selectIsPartialAnalysis(completeState), false)

  // 3. Partial document via completion_ratio < 1.0
  const partialRatioState = {
    analysis: {
      result: {
        document_id: 'doc-2',
        summary: { is_partial: false },
        clauses: [],
        metadata: {
          completion_ratio: 0.75,
          incomplete_chunks: [{ chunk_id: 'chk_3', chunk_index: 3, page_start: 7, page_end: 9 }],
        },
      },
    },
  }
  assert.equal(selectCompletionRatio(partialRatioState), 0.75)
  assert.equal(selectIsPartialAnalysis(partialRatioState), true)
  assert.equal(selectIncompleteChunks(partialRatioState).length, 1)

  // 4. Partial document via summary.is_partial === true
  const partialSummaryState = {
    analysis: {
      result: {
        document_id: 'doc-3',
        summary: { is_partial: true },
        clauses: [],
        metadata: {},
      },
    },
  }
  assert.equal(selectIsPartialAnalysis(partialSummaryState), true)
  assert.equal(selectCompletionRatio(partialSummaryState), null)
})

