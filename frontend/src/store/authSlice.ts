import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import type { AuthState, User, LoginResponse } from '../types'
import { apiClient, googleSignIn } from '../services/api'

// ─── Async thunks ────────────────────────────────────────────────────────────

export const loginUser = createAsyncThunk(
  'auth/login',
  async (credentials: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const formData = new FormData()
      formData.append('username', credentials.email)
      formData.append('password', credentials.password)
      const response = await apiClient.post<LoginResponse>('/auth/login', formData)
      localStorage.setItem('sl_token', response.data.access_token)
      return response.data
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Login failed')
    }
  }
)

export const registerUser = createAsyncThunk(
  'auth/register',
  async (data: { name: string; email: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<LoginResponse>('/auth/register', data)
      localStorage.setItem('sl_token', response.data.access_token)
      return response.data
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Registration failed')
    }
  }
)

export const loginWithGoogle = createAsyncThunk(
  'auth/googleLogin',
  async (credential: string, { rejectWithValue }) => {
    try {
      const data = await googleSignIn(credential)
      localStorage.setItem('sl_token', data.access_token)
      return data as LoginResponse
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      return rejectWithValue(error.response?.data?.detail || 'Google sign-in failed')
    }
  }
)

export const fetchCurrentUser = createAsyncThunk(
  'auth/me',
  async (_, { rejectWithValue }) => {
    try {
      const response = await apiClient.get<User>('/auth/me')
      return response.data
    } catch {
      return rejectWithValue('Session expired')
    }
  }
)

// ─── Initial state ────────────────────────────────────────────────────────────

const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('sl_token'),
  isLoading: false,
  error: null,
}

// ─── Slice ────────────────────────────────────────────────────────────────────

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout(state) {
      state.user = null
      state.token = null
      state.error = null
      localStorage.removeItem('sl_token')
    },
    clearAuthError(state) {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    // Login
    builder
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(loginUser.fulfilled, (state, action: PayloadAction<LoginResponse>) => {
        state.isLoading = false
        state.user = action.payload.user
        state.token = action.payload.access_token
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // Register
    builder
      .addCase(registerUser.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(registerUser.fulfilled, (state, action: PayloadAction<LoginResponse>) => {
        state.isLoading = false
        state.user = action.payload.user
        state.token = action.payload.access_token
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // Google Login
    builder
      .addCase(loginWithGoogle.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(loginWithGoogle.fulfilled, (state, action: PayloadAction<LoginResponse>) => {
        state.isLoading = false
        state.user = action.payload.user
        state.token = action.payload.access_token
      })
      .addCase(loginWithGoogle.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // Fetch current user
    builder
      .addCase(fetchCurrentUser.fulfilled, (state, action: PayloadAction<User>) => {
        state.user = action.payload
      })
      .addCase(fetchCurrentUser.rejected, (state) => {
        state.user = null
        state.token = null
        localStorage.removeItem('sl_token')
      })
  },
})

export const { logout, clearAuthError } = authSlice.actions
export default authSlice.reducer