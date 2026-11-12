import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import type { AnalysisState, AnalysisResult, FrontendAnalysisState } from '../types'
import { apiClient } from '../services/api'

type AnalyzeDocumentArgs =
  | string
  | {
      documentId: string
      forceReanalyze?: boolean
    }

function normalizeAnalyzeArgs(args: AnalyzeDocumentArgs) {
  if (typeof args === 'string') {
    return { documentId: args, forceReanalyze: false }
  }
  return {
    documentId: args.documentId,
    forceReanalyze: Boolean(args.forceReanalyze),
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

export function deriveAnalysisState(
  result: AnalysisResult | null,
  isLoading: boolean,
  error: string | null,
  retryAfterRemaining?: number | null,
  isRetryingProvider?: boolean
): FrontendAnalysisState | null {
  // If actively retrying after a provider cooldown/rate-limit, preserve retrying context
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
  // Check partial failure:
  const isPartial =
    result.summary?.is_partial === true ||
    (result.metadata?.completion_ratio != null && result.metadata.completion_ratio < 1.0) ||
    (result.metadata?.incomplete_chunks != null && result.metadata.incomplete_chunks.length > 0)

  if (isPartial) {
    return 'partial'
  }

  // Check uncertainty: presence of [UNCLEAR] in clauses or plain translations
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

/** Sleep that rejects immediately if the AbortSignal fires. */
function abortableSleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) return reject(new DOMException('Aborted', 'AbortError'))
    const timer = setTimeout(resolve, ms)
    signal?.addEventListener(
      'abort',
      () => {
        clearTimeout(timer)
        reject(new DOMException('Aborted', 'AbortError'))
      },
      { once: true }
    )
  })
}

/** Poll GET /analyze/{id}/status until status is "done" or "error".
 *  Stops early (and cancels the in-flight request) when `signal` aborts —
 *  e.g. the user navigated away from the analysis page. */
async function pollUntilDone(
  documentId: string,
  onTick?: (elapsedSec: number) => void,
  signal?: AbortSignal,
  onProgress?: (stage: string | null, pct: number | null) => void
): Promise<AnalysisResult> {
  const INITIAL_INTERVAL_MS = 3000
  const MAX_INTERVAL_MS = 15000
  // Long documents on free-tier AI limits can legitimately take up to ~1 hour (server-side budget).
  const MAX_WAIT_MS = 62 * 60 * 1000
  const startTime = Date.now()
  const deadline = startTime + MAX_WAIT_MS
  let intervalMs = INITIAL_INTERVAL_MS

  while (Date.now() < deadline) {
    if (signal?.aborted) throw new DOMException('Aborted', 'AbortError')
    await abortableSleep(intervalMs, signal)
    if (onTick) {
      onTick(Math.round((Date.now() - startTime) / 1000))
    }

    const { data } = await apiClient.get<{
      status: 'processing' | 'done' | 'error'
      analysis?: AnalysisResult
      error?: string
      stage?: string
      progress_pct?: number
    }>(`/analyze/${documentId}/status`, { signal })

    if (data.status === 'processing' && onProgress) {
      onProgress(data.stage ?? null, typeof data.progress_pct === 'number' ? data.progress_pct : null)
    }

    if (data.status === 'done' && data.analysis) {
      return data.analysis
    }
    if (data.status === 'error') {
      throw new Error(data.error ?? 'Analysis failed on the server.')
    }
    // A processing response is expected for a background job. Back off rather
    // than hammering the status endpoint if extraction/OCR/model calls are slow.
    intervalMs = Math.min(MAX_INTERVAL_MS, Math.round(intervalMs * 1.5))
  }

  throw new Error('Analysis is still processing after an hour. Automatic status checks have stopped; please check again or retry the analysis.')
}

// ── Async thunks ──────────────────────────────────────────────────────────────

export const analyzeDocument = createAsyncThunk(
  'analysis/analyze',
  async (args: AnalyzeDocumentArgs, { dispatch, getState, rejectWithValue, signal }) => {
    const { documentId, forceReanalyze } = normalizeAnalyzeArgs(args)
    try {
      const current = (getState() as { analysis: AnalysisState }).analysis
      const wasProviderUnavailable =
        current.state === 'provider_unavailable' ||
        current.state === 'retrying_provider' ||
        Boolean(current.isRetryingProvider) ||
        (current.error != null && (
          current.error.toLowerCase().includes('cooloff') ||
          current.error.toLowerCase().includes('rate limit') ||
          current.error.toLowerCase().includes('rate-limit') ||
          current.error.toLowerCase().includes('503') ||
          current.error.toLowerCase().includes('service unavailable')
        ))

      dispatch(analysisSlice.actions.setAnalysisState(wasProviderUnavailable ? 'retrying_provider' : 'queued'))

      // Kick off analysis (may return immediately with cached result, or 202 processing)
      const { data } = await apiClient.post<
        | { analysis: AnalysisResult }           // cached hit
        | { status: 'processing'; document_id: string }  // background task started
      >('/analyze', {
        document_id: documentId,
        force_reanalyze: forceReanalyze,
      }, { signal })

      // Cached result returned straight away
      if ('analysis' in data) return data.analysis

      // Background task — poll until done (cancellable) with elapsed time updates
      dispatch(analysisSlice.actions.setAnalysisState(wasProviderUnavailable ? 'retrying_provider' : 'processing'))
      return await pollUntilDone(
        documentId,
        (sec) => dispatch(analysisSlice.actions.setElapsedSeconds(sec)),
        signal,
        (stage, pct) => dispatch(analysisSlice.actions.setJobProgress({ stage, pct }))
      )
    } catch (err: unknown) {
      const error = err as {
        name?: string
        code?: string
        message?: string
        response?: {
          status?: number
          data?: { detail?: string; error?: string; retry_after?: number }
        }
      }
      // Cancelled (navigated away) — don't surface as an error.
      if (error.name === 'AbortError' || error.name === 'CanceledError' || error.code === 'ERR_CANCELED') {
        return rejectWithValue('cancelled')
      }

      const status = error.response?.status
      const detail =
        error.response?.data?.detail ??
        error.response?.data?.error ??
        error.message ??
        'Analysis failed'
      const retryAfter = error.response?.data?.retry_after

      if (
        status === 429 ||
        status === 503 ||
        detail.toLowerCase().includes('rate limit') ||
        detail.toLowerCase().includes('rate-limit') ||
        detail.toLowerCase().includes('cooloff') ||
        detail.toLowerCase().includes('too many concurrent') ||
        detail.toLowerCase().includes('service unavailable') ||
        detail.toLowerCase().includes('503')
      ) {
        return rejectWithValue({
          message: detail,
          isRateLimit: true,
          retryAfter: typeof retryAfter === 'number' && retryAfter > 0 ? retryAfter : null,
        })
      }

      return rejectWithValue(detail)
    }
  }
)

/** Re-analyzes the entire document (including unanalyzed sections) via POST /analyze with force_reanalyze: true. */
export const retryMissingChunks = createAsyncThunk(
  'analysis/retryMissingChunks',
  async (documentId: string, { dispatch }) => {
    return await dispatch(analyzeDocument({ documentId, forceReanalyze: true })).unwrap()
  }
)

export const analyzeComparisonDocument = createAsyncThunk(
  'analysis/analyzeComparison',
  async (args: AnalyzeDocumentArgs, { rejectWithValue }) => {
    const { documentId, forceReanalyze } = normalizeAnalyzeArgs(args)
    try {
      const { data } = await apiClient.post<
        | { analysis: AnalysisResult }
        | { status: 'processing'; document_id: string }
      >('/analyze', {
        document_id: documentId,
        force_reanalyze: forceReanalyze,
      })

      if ('analysis' in data) return data.analysis
      return await pollUntilDone(documentId)
    } catch (err: unknown) {
      const error = err as {
        message?: string
        response?: { data?: { detail?: string } }
      }
      return rejectWithValue(
        error.response?.data?.detail ?? error.message ?? 'Analysis failed'
      )
    }
  }
)

// ── Initial state ─────────────────────────────────────────────────────────────

const initialState: AnalysisState = {
  result: null,
  comparisonResult: null,
  isLoading: false,
  error: null,
  state: undefined,
  elapsedSeconds: 0,
  retryAfterRemaining: null,
  isRetryingProvider: false,
}

// ── Slice ─────────────────────────────────────────────────────────────────────

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    clearAnalysis(state) {
      state.result = null
      state.comparisonResult = null
      state.error = null
      state.state = undefined
      state.elapsedSeconds = 0
      state.retryAfterRemaining = null
      state.isRetryingProvider = false
    },
    clearAnalysisError(state) {
      state.error = null
      state.retryAfterRemaining = null
      state.isRetryingProvider = false
      state.state = deriveAnalysisState(state.result, state.isLoading, null) || undefined
    },
    setAnalysisState(state, action: PayloadAction<AnalysisState['state']>) {
      state.state = action.payload
    },
    setElapsedSeconds(state, action: PayloadAction<number>) {
      state.elapsedSeconds = action.payload
    },
    setJobProgress(state, action: PayloadAction<{ stage: string | null; pct: number | null }>) {
      state.jobStage = action.payload.stage
      state.jobProgress = action.payload.pct
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(analyzeDocument.pending, (state) => {
        const wasProviderUnavailable =
          state.state === 'provider_unavailable' ||
          state.state === 'retrying_provider' ||
          Boolean(state.isRetryingProvider) ||
          (state.error != null && (
            state.error.toLowerCase().includes('cooloff') ||
            state.error.toLowerCase().includes('rate limit') ||
            state.error.toLowerCase().includes('rate-limit') ||
            state.error.toLowerCase().includes('503') ||
            state.error.toLowerCase().includes('service unavailable')
          ))
        state.isLoading = true
        state.isRetryingProvider = wasProviderUnavailable
        state.error = null
        state.state = wasProviderUnavailable ? 'retrying_provider' : 'queued'
        state.elapsedSeconds = 0
        state.retryAfterRemaining = null
        state.jobStage = null
        state.jobProgress = null
      })
      .addCase(analyzeDocument.fulfilled, (state, action: PayloadAction<AnalysisResult>) => {
        state.isLoading = false
        state.isRetryingProvider = false
        state.result = action.payload
        state.state = deriveAnalysisState(action.payload, false, null) || 'completed'
      })
      .addCase(analyzeDocument.rejected, (state, action) => {
        state.isLoading = false
        state.isRetryingProvider = false
        if (action.payload === 'cancelled') {
          state.error = null
          state.state = undefined
          return
        }
        if (
          typeof action.payload === 'object' &&
          action.payload !== null &&
          'isRateLimit' in action.payload
        ) {
          const payloadObj = action.payload as {
            message: string
            isRateLimit: boolean
            retryAfter: number | null
          }
          state.error = payloadObj.message
          state.state = 'provider_unavailable'
          state.retryAfterRemaining = payloadObj.retryAfter
          return
        }
        const errorMsg = (action.payload as string) || 'Analysis failed'
        state.error = errorMsg
        state.state = deriveAnalysisState(null, false, errorMsg) || 'failed'
      })

    builder.addCase(
      analyzeComparisonDocument.fulfilled,
      (state, action: PayloadAction<AnalysisResult>) => {
        state.comparisonResult = action.payload
      }
    )
  },
})

export const { clearAnalysis, clearAnalysisError, setAnalysisState, setElapsedSeconds, setJobProgress } =
  analysisSlice.actions

// ── Phase 8A Selectors & Metadata Accessors ──────────────────────────────────

export const selectAnalysisResult = (state: { analysis: AnalysisState }) => state.analysis.result
export const selectAnalysisMetadata = (state: { analysis: AnalysisState }) => state.analysis.result?.metadata
export const selectCompletionRatio = (state: { analysis: AnalysisState }): number | null =>
  state.analysis.result?.metadata?.completion_ratio ?? null
export const selectIncompleteChunks = (state: { analysis: AnalysisState }) =>
  state.analysis.result?.metadata?.incomplete_chunks ?? []
export const selectOptimizationTelemetry = (state: { analysis: AnalysisState }) =>
  state.analysis.result?.metadata?.optimization
export const selectIsPartialAnalysis = (state: { analysis: AnalysisState }): boolean => {
  const result = state.analysis.result
  if (!result) return false
  return (
    result.summary?.is_partial === true ||
    (result.metadata?.completion_ratio != null && result.metadata.completion_ratio < 1.0) ||
    Boolean(result.metadata?.incomplete_chunks && result.metadata.incomplete_chunks.length > 0)
  )
}
export const selectOcrConfidence = (state: { analysis: AnalysisState }): number | null =>
  state.analysis.result?.metadata?.ocr_confidence ?? null

export default analysisSlice.reducer
