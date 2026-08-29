import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import type { ChatMessage, ChatResponse } from '../types'
import { apiClient } from '../services/api'

// The advisor conversation is kept per-browser so it survives navigation/reloads.
const STORAGE_KEY = 'sl_advisor_chat'

function loadMessages(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? (parsed as ChatMessage[]) : []
  } catch {
    return []
  }
}

function persist(messages: ChatMessage[]) {
  try {
    // Keep the stored transcript bounded.
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-50)))
  } catch {
    /* ignore quota / private-mode errors */
  }
}

interface AdvisorState {
  messages: ChatMessage[]
  isLoading: boolean
  error: string | null
}

const initialState: AdvisorState = {
  messages: loadMessages(),
  isLoading: false,
  error: null,
}

export const sendAdvisorMessage = createAsyncThunk(
  'advisor/send',
  async (message: string, { getState, rejectWithValue }) => {
    try {
      const { advisor } = getState() as { advisor: AdvisorState }
      // Exclude the just-added current user message — it is sent separately as `message`.
      const prior = advisor.messages.slice(0, -1)
      const history = prior.slice(-12).map((m) => ({ role: m.role, content: m.content }))
      const response = await apiClient.post<ChatResponse>('/advisor', { message, history })
      return response.data.message
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string }; status?: number } }
      if (error.response?.status === 401) return rejectWithValue('Please sign in to consult the legal advisor.')
      return rejectWithValue(error.response?.data?.detail || 'The advisor could not respond. Please try again.')
    }
  }
)

const advisorSlice = createSlice({
  name: 'advisor',
  initialState,
  reducers: {
    addAdvisorUserMessage(state, action: PayloadAction<string>) {
      state.messages.push({
        id: `adv_${Date.now()}`,
        role: 'user',
        content: action.payload,
        timestamp: new Date().toISOString(),
      })
      persist(state.messages)
    },
    clearAdvisor(state) {
      state.messages = []
      state.error = null
      persist(state.messages)
    },
    clearAdvisorError(state) {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendAdvisorMessage.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(sendAdvisorMessage.fulfilled, (state, action: PayloadAction<ChatMessage>) => {
        state.isLoading = false
        state.messages.push(action.payload)
        persist(state.messages)
      })
      .addCase(sendAdvisorMessage.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
  },
})

export const { addAdvisorUserMessage, clearAdvisor, clearAdvisorError } = advisorSlice.actions
export default advisorSlice.reducer
