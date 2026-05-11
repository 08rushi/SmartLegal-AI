import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import type { DocumentState, UploadedDocument, UploadResponse } from '../types'
import { apiClient } from '../services/api'

// ─── Async thunks ────────────────────────────────────────────────────────────

export const uploadDocument = createAsyncThunk(
  'document/upload',
  async (file: File, { rejectWithValue, dispatch }) => {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await apiClient.post<UploadResponse>('/upload', formData, {
        onUploadProgress: (progressEvent) => {
          const pct = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total ?? 1)
          )
          dispatch(setUploadProgress(pct))
        },
      })
      return response.data.document
    } catch (err: unknown) {
      const error = err as {
        code?: string
        message?: string
        response?: { data?: { detail?: string } }
      }
      return rejectWithValue(
        error.response?.data?.detail ||
          (error.code === 'ERR_NETWORK'
            ? 'Upload failed. Make sure the backend is running on http://localhost:8000.'
            : error.message || 'Upload failed')
      )
    }
  }
)

export const uploadComparisonDocument = createAsyncThunk(
  'document/uploadComparison',
  async (file: File, { rejectWithValue }) => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await apiClient.post<UploadResponse>('/upload', formData)
      return response.data.document
    } catch (err: unknown) {
      const error = err as {
        code?: string
        message?: string
        response?: { data?: { detail?: string } }
      }
      return rejectWithValue(
        error.response?.data?.detail ||
          (error.code === 'ERR_NETWORK'
            ? 'Upload failed. Make sure the backend is running on http://localhost:8000.'
            : error.message || 'Upload failed')
      )
    }
  }
)

// ── NEW: fetch full history from backend (called after login/page load) ───────
export const fetchDocumentHistory = createAsyncThunk(
  'document/fetchHistory',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<{ documents: UploadedDocument[] }>('/upload/history')
      return response.data.documents
    } catch (err: unknown) {
      const error = err as { response?: { status?: number } }
      // 401 = not logged in — silently ignore, history stays empty
      if (error.response?.status === 401) return []
      return rejectWithValue('Failed to load document history')
    }
  }
)

export const fetchDocumentById = createAsyncThunk(
  'document/fetchById',
  async (documentId: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<UploadedDocument>(`/upload/${documentId}`)
      return response.data
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to load document')
    }
  }
)

// ─── Initial state ─────────────────────────────────────────────────────────────

const initialState: DocumentState = {
  current: null,
  comparison: null,
  history: [],
  uploadProgress: 0,
  status: 'idle',
  error: null,
}

// ─── Slice ────────────────────────────────────────────────────────────────────

const documentSlice = createSlice({
  name: 'document',
  initialState,
  reducers: {
    setUploadProgress(state, action: PayloadAction<number>) {
      state.uploadProgress = action.payload
    },
    clearDocument(state) {
      state.current = null
      state.status = 'idle'
      state.error = null
      state.uploadProgress = 0
    },
    clearComparison(state) {
      state.comparison = null
    },
    clearDocumentError(state) {
      state.error = null
    },
    setCurrentDocument(state, action: PayloadAction<UploadedDocument | null>) {
      state.current = action.payload
      if (action.payload && !state.history.find((doc) => doc.id === action.payload?.id)) {
        state.history.unshift(action.payload)
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(uploadDocument.pending, (state) => {
        state.status = 'uploading'
        state.error = null
        state.uploadProgress = 0
      })
      .addCase(uploadDocument.fulfilled, (state, action: PayloadAction<UploadedDocument>) => {
        state.status = 'ready'
        state.current = action.payload
        state.uploadProgress = 100
        // Prepend to history if not already there
        if (!state.history.find(d => d.id === action.payload.id)) {
          state.history.unshift(action.payload)
        }
      })
      .addCase(uploadDocument.rejected, (state, action) => {
        state.status = 'error'
        state.error = action.payload as string
        state.uploadProgress = 0
      })

    builder
      .addCase(uploadComparisonDocument.fulfilled, (state, action: PayloadAction<UploadedDocument>) => {
        state.comparison = action.payload
      })

    // Fetch history from backend — replaces in-memory list with real DB data
    builder
      .addCase(fetchDocumentHistory.fulfilled, (state, action: PayloadAction<UploadedDocument[]>) => {
        if (action.payload.length > 0) {
          state.history = action.payload
          // Keep current pointer valid if it exists in the fresh list
          if (state.current) {
            const fresh = action.payload.find(d => d.id === state.current?.id)
            if (fresh) state.current = fresh
          }
        }
      })

    builder.addCase(fetchDocumentById.fulfilled, (state, action: PayloadAction<UploadedDocument>) => {
      state.current = action.payload
      if (!state.history.find((doc) => doc.id === action.payload.id)) {
        state.history.unshift(action.payload)
      }
    })
  },
})

export const {
  setUploadProgress,
  clearDocument,
  clearComparison,
  clearDocumentError,
  setCurrentDocument,
} = documentSlice.actions
export default documentSlice.reducer
