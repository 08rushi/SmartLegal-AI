import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import type { AnalysisState, AnalysisResult, AnalyzeResponse } from '../types'
import { apiClient } from '../services/api'

// ─── Async thunks ────────────────────────────────────────────────────────────

export const analyzeDocument = createAsyncThunk(
  'analysis/analyze',
  async (documentId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<AnalyzeResponse>('/analyze', {
        document_id: documentId,
      })
      return response.data.analysis
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Analysis failed')
    }
  }
)

export const analyzeComparisonDocument = createAsyncThunk(
  'analysis/analyzeComparison',
  async (documentId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<AnalyzeResponse>('/analyze', {
        document_id: documentId,
      })
      return response.data.analysis
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Analysis failed')
    }
  }
)

// ─── Initial state ────────────────────────────────────────────────────────────

const initialState: AnalysisState = {
  result: null,
  comparisonResult: null,
  isLoading: false,
  error: null,
}

// ─── Slice ────────────────────────────────────────────────────────────────────

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
        state.error = action.payload as string
      })

    builder
      .addCase(analyzeComparisonDocument.fulfilled, (state, action: PayloadAction<AnalysisResult>) => {
        state.comparisonResult = action.payload
      })
  },
})

export const { clearAnalysis, clearAnalysisError } = analysisSlice.actions
export default analysisSlice.reducer
