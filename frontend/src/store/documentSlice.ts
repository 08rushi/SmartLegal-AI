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

// ─── Initial state ────────────────────────────────────────────────────────────

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
        // Add to history if not already there
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
  },
})

export const { setUploadProgress, clearDocument, clearComparison, clearDocumentError } = documentSlice.actions
export default documentSlice.reducer
