import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import type { AnalysisState, AnalysisResult } from '../types'
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
async function pollUntilDone(documentId: string, signal?: AbortSignal): Promise<AnalysisResult> {
  const INTERVAL_MS = 3000   // check every 3 s
  const MAX_WAIT_MS = 5 * 60 * 1000  // give up after 5 min

  const deadline = Date.now() + MAX_WAIT_MS

  while (Date.now() < deadline) {
    if (signal?.aborted) throw new DOMException('Aborted', 'AbortError')
    await abortableSleep(INTERVAL_MS, signal)

    const { data } = await apiClient.get<{
      status: 'processing' | 'done' | 'error'
      analysis?: AnalysisResult
      error?: string
    }>(`/analyze/${documentId}/status`, { signal })

    if (data.status === 'done' && data.analysis) {
      return data.analysis
    }
    if (data.status === 'error') {
      throw new Error(data.error ?? 'Analysis failed on the server.')
    }
    // still "processing" — keep polling
  }

  throw new Error('Analysis timed out. The document may be too large — please try again.')
}

// ── Async thunks ──────────────────────────────────────────────────────────────

export const analyzeDocument = createAsyncThunk(
  'analysis/analyze',
  async (args: AnalyzeDocumentArgs, { rejectWithValue, signal }) => {
    const { documentId, forceReanalyze } = normalizeAnalyzeArgs(args)
    try {
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

      // Background task — poll until done (cancellable)
      return await pollUntilDone(documentId, signal)
    } catch (err: unknown) {
      const error = err as {
        name?: string
        code?: string
        message?: string
        response?: { data?: { detail?: string } }
      }
      // Cancelled (navigated away) — don't surface as an error.
      if (error.name === 'AbortError' || error.name === 'CanceledError' || error.code === 'ERR_CANCELED') {
        return rejectWithValue('cancelled')
      }
      return rejectWithValue(
        error.response?.data?.detail ?? error.message ?? 'Analysis failed'
      )
    }
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
    },
    clearAnalysisError(state) {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(analyzeDocument.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(analyzeDocument.fulfilled, (state, action: PayloadAction<AnalysisResult>) => {
        state.isLoading = false
        state.result = action.payload
      })
      .addCase(analyzeDocument.rejected, (state, action) => {
        state.isLoading = false
        // A cancelled request (user navigated away) is not a real error.
        state.error = action.payload === 'cancelled' ? null : (action.payload as string)
      })

    builder.addCase(
      analyzeComparisonDocument.fulfilled,
      (state, action: PayloadAction<AnalysisResult>) => {
        state.comparisonResult = action.payload
      }
    )
  },
})

export const { clearAnalysis, clearAnalysisError } = analysisSlice.actions
export default analysisSlice.reducer
