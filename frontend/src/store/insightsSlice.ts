import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { ConsequenceResult, InsightsState, NegotiationResult } from '../types'
import { apiClient } from '../services/api'

const initialState: InsightsState = {
  documentId: null,
  consequences: null,
  negotiation: null,
  consequencesStatus: 'idle',
  negotiationStatus: 'idle',
  error: null,
}

export const fetchConsequences = createAsyncThunk(
  'insights/consequences',
  async ({ documentId, force = false }: { documentId: string; force?: boolean }, { rejectWithValue }) => {
    try {
      const res = await apiClient.post<{ consequences: ConsequenceResult }>(
        `/insights/${documentId}/consequences${force ? '?force=true' : ''}`,
      )
      return res.data.consequences
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string }; status?: number } }
      if (e.response?.status === 401) return rejectWithValue('Please sign in to use this feature.')
      return rejectWithValue(e.response?.data?.detail || 'Could not generate the "what if I sign" simulation.')
    }
  },
)

export const fetchNegotiation = createAsyncThunk(
  'insights/negotiation',
  async ({ documentId, force = false }: { documentId: string; force?: boolean }, { rejectWithValue }) => {
    try {
      const res = await apiClient.post<{ negotiation: NegotiationResult }>(
        `/insights/${documentId}/negotiation${force ? '?force=true' : ''}`,
      )
      return res.data.negotiation
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string }; status?: number } }
      if (e.response?.status === 401) return rejectWithValue('Please sign in to use this feature.')
      return rejectWithValue(e.response?.data?.detail || 'Could not generate negotiation guidance.')
    }
  },
)

const insightsSlice = createSlice({
  name: 'insights',
  initialState,
  reducers: {
    // Reset all insights when the active document changes so nothing bleeds across docs.
    setInsightsDocument(state, action: PayloadAction<string>) {
      if (state.documentId !== action.payload) {
        state.documentId = action.payload
        state.consequences = null
        state.negotiation = null
        state.consequencesStatus = 'idle'
        state.negotiationStatus = 'idle'
        state.error = null
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchConsequences.pending, (state) => {
        state.consequencesStatus = 'loading'
        state.error = null
      })
      .addCase(fetchConsequences.fulfilled, (state, action: PayloadAction<ConsequenceResult>) => {
        state.consequencesStatus = 'ready'
        state.consequences = action.payload
      })
      .addCase(fetchConsequences.rejected, (state, action) => {
        state.consequencesStatus = 'error'
        state.error = action.payload as string
      })
      .addCase(fetchNegotiation.pending, (state) => {
        state.negotiationStatus = 'loading'
        state.error = null
      })
      .addCase(fetchNegotiation.fulfilled, (state, action: PayloadAction<NegotiationResult>) => {
        state.negotiationStatus = 'ready'
        state.negotiation = action.payload
      })
      .addCase(fetchNegotiation.rejected, (state, action) => {
        state.negotiationStatus = 'error'
        state.error = action.payload as string
      })
  },
})

export const { setInsightsDocument } = insightsSlice.actions
export default insightsSlice.reducer
