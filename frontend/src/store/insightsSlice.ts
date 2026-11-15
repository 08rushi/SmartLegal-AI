import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { ConsequenceResult, InsightsState, NegotiationResult } from '../types'
import { apiClient } from '../services/api'
import { apiErrorMessage } from '../utils/apiError'
import i18n from '../i18n'

const initialState: InsightsState = {
  documentId: null,
  consequences: null,
  negotiation: null,
  consequencesStatus: 'idle',
  negotiationStatus: 'idle',
  consequencesLang: null,
  negotiationLang: null,
  error: null,
}

export const fetchConsequences = createAsyncThunk(
  'insights/consequences',
  // `lang` = the language the request is made in (X-Lang is sent by the axios interceptor); the backend
  // generates and caches this insight per language.
  async ({ documentId, force = false }: { documentId: string; force?: boolean; lang: string }, { rejectWithValue }) => {
    try {
      const res = await apiClient.post<{ consequences: ConsequenceResult }>(
        `/insights/${documentId}/consequences${force ? '?force=true' : ''}`,
      )
      return res.data.consequences
    } catch (err: unknown) {
      const e = err as { response?: { status?: number } }
      if (e.response?.status === 401) return rejectWithValue(i18n.t('store:insights.signIn'))
      return rejectWithValue(apiErrorMessage(err, 'store:insights.simulateFailed'))
    }
  },
)

export const fetchNegotiation = createAsyncThunk(
  'insights/negotiation',
  // `lang` = the language the request is made in (X-Lang is sent by the axios interceptor); the backend
  // generates and caches this insight per language.
  async ({ documentId, force = false }: { documentId: string; force?: boolean; lang: string }, { rejectWithValue }) => {
    try {
      const res = await apiClient.post<{ negotiation: NegotiationResult }>(
        `/insights/${documentId}/negotiation${force ? '?force=true' : ''}`,
      )
      return res.data.negotiation
    } catch (err: unknown) {
      const e = err as { response?: { status?: number } }
      if (e.response?.status === 401) return rejectWithValue(i18n.t('store:insights.signIn'))
      return rejectWithValue(apiErrorMessage(err, 'store:insights.negotiateFailed'))
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
        state.consequencesLang = null
        state.negotiationLang = null
        state.error = null
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchConsequences.pending, (state, action) => {
        state.consequencesStatus = 'loading'
        state.consequencesLang = action.meta.arg.lang
        state.error = null
      })
      .addCase(fetchConsequences.fulfilled, (state, action: PayloadAction<ConsequenceResult, string, { arg: { lang: string } }>) => {
        // Ignore a response for a language the user has already switched away from.
        if (state.consequencesLang !== action.meta.arg.lang) return
        state.consequencesStatus = 'ready'
        state.consequences = action.payload
      })
      .addCase(fetchConsequences.rejected, (state, action) => {
        if (state.consequencesLang !== action.meta.arg.lang) return
        state.consequencesStatus = 'error'
        state.error = action.payload as string
      })
      .addCase(fetchNegotiation.pending, (state, action) => {
        state.negotiationStatus = 'loading'
        state.negotiationLang = action.meta.arg.lang
        state.error = null
      })
      .addCase(fetchNegotiation.fulfilled, (state, action: PayloadAction<NegotiationResult, string, { arg: { lang: string } }>) => {
        if (state.negotiationLang !== action.meta.arg.lang) return
        state.negotiationStatus = 'ready'
        state.negotiation = action.payload
      })
      .addCase(fetchNegotiation.rejected, (state, action) => {
        if (state.negotiationLang !== action.meta.arg.lang) return
        state.negotiationStatus = 'error'
        state.error = action.payload as string
      })
  },
})

export const { setInsightsDocument } = insightsSlice.actions
export default insightsSlice.reducer
