import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import type { ChatState, ChatMessage, ChatResponse } from '../types'
import { apiClient } from '../services/api'

// ─── Async thunks ────────────────────────────────────────────────────────────

export const sendChatMessage = createAsyncThunk(
  'chat/sendMessage',
  async (
    payload: { document_id: string; question: string },
    { rejectWithValue }
  ) => {
    try {
      const response = await apiClient.post<ChatResponse>('/chat', {
        document_id: payload.document_id,
        question: payload.question,
      })
      return response.data.message
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Failed to get answer')
    }
  }
)

// ─── Initial state ────────────────────────────────────────────────────────────

const initialState: ChatState = {
  messages: [],
  isLoading: false,
  error: null,
  document_id: null,
}

// ─── Slice ────────────────────────────────────────────────────────────────────

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setDocumentId(state, action: PayloadAction<string>) {
      state.document_id = action.payload
    },
    addUserMessage(state, action: PayloadAction<string>) {
      const message: ChatMessage = {
        id: `msg_${Date.now()}`,
        role: 'user',
        content: action.payload,
        timestamp: new Date().toISOString(),
      }
      state.messages.push(message)
    },
    clearChat(state) {
      state.messages = []
      state.error = null
      state.document_id = null
    },
    clearChatError(state) {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(sendChatMessage.fulfilled, (state, action: PayloadAction<ChatMessage>) => {
        state.isLoading = false
        state.messages.push(action.payload)
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
  },
})

export const { setDocumentId, addUserMessage, clearChat, clearChatError } = chatSlice.actions
export default chatSlice.reducer
