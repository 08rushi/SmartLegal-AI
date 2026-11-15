import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import type { AuthState, User, LoginResponse } from '../types'
import { apiClient, googleSignIn } from '../services/api'
import { apiErrorMessage } from '../utils/apiError'
import i18n from '../i18n'

// ─── Async thunks ────────────────────────────────────────────────────────────

export const loginUser = createAsyncThunk(
  'auth/login',
  async (credentials: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const formData = new FormData()
      formData.append('username', credentials.email)
      formData.append('password', credentials.password)
      const response = await apiClient.post<LoginResponse>('/auth/login', formData)
      return response.data
    } catch (err: unknown) {
      // No HTTP response at all = server down / offline / CORS block -> translated network message.
      return rejectWithValue(apiErrorMessage(err, 'store:auth.loginFailed'))
    }
  }
)

export const registerUser = createAsyncThunk(
  'auth/register',
  async (data: { name: string; email: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<LoginResponse>('/auth/register', data)
      return response.data
    } catch (err: unknown) {
      // FastAPI validation errors (422) come back as a list of {msg}; apiErrorMessage joins them.
      return rejectWithValue(apiErrorMessage(err, 'store:auth.registerFailed'))
    }
  }
)

export const loginWithGoogle = createAsyncThunk(
  'auth/googleLogin',
  async (credential: string, { rejectWithValue }) => {
    try {
      const data = await googleSignIn(credential)
      return data as LoginResponse
    } catch (err: unknown) {
      return rejectWithValue(apiErrorMessage(err, 'store:auth.googleFailed'))
    }
  }
)

export const forgotPassword = createAsyncThunk(
  'auth/forgotPassword',
  async (email: string, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<{ message: string; reset_token?: string }>(
        '/auth/forgot-password',
        { email }
      )
      return response.data
    } catch (err: unknown) {
      return rejectWithValue(apiErrorMessage(err, 'store:auth.forgotFailed'))
    }
  }
)

export const resetPassword = createAsyncThunk(
  'auth/resetPassword',
  async (payload: { token: string; new_password: string }, { rejectWithValue }) => {
    try {
      const response = await apiClient.post<{ message: string }>('/auth/reset-password', payload)
      return response.data
    } catch (err: unknown) {
      return rejectWithValue(apiErrorMessage(err, 'store:auth.resetFailed'))
    }
  }
)

export const logoutAllSessions = createAsyncThunk(
  'auth/logoutAll',
  async (_, { rejectWithValue }) => {
    try {
      await apiClient.post('/auth/logout-all')
      return true
    } catch (err: unknown) {
      return rejectWithValue(apiErrorMessage(err, 'store:auth.logoutAllFailed'))
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
      // 401 (no/expired cookie) or unreachable server: no confirmed session.
      return rejectWithValue(i18n.t('store:auth.sessionExpired'))
    }
  }
)

/** Sign out: the server clears the HttpOnly cookie; local state is cleared immediately regardless. */
export const logout = createAsyncThunk('auth/logout', async () => {
  try {
    await apiClient.post('/auth/logout')
  } catch {
    /* already signed out / offline: local state is cleared anyway */
  }
})

// ─── Initial state ────────────────────────────────────────────────────────────

// Sessions live in the HttpOnly `sl_token` cookie only. Remove any token left in localStorage by older builds.
try {
  localStorage.removeItem('sl_token')
} catch {
  /* storage blocked: nothing to clean */
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  // false until the first GET /auth/me (cookie session restore) settles, so guards don't flash "sign in".
  sessionChecked: false,
  isLoading: false,
  error: null,
}

function signIn(state: AuthState, user: User) {
  state.isLoading = false
  state.user = user
  state.isAuthenticated = true
  state.sessionChecked = true
}

function signOut(state: AuthState) {
  state.user = null
  state.isAuthenticated = false
  state.error = null
}

// ─── Slice ────────────────────────────────────────────────────────────────────

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    /** Dispatched by the API layer on a 401 from an authenticated call: drop local user state. */
    sessionExpired(state) {
      signOut(state)
      state.sessionChecked = true
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
        signIn(state, action.payload.user)
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
        signIn(state, action.payload.user)
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
        signIn(state, action.payload.user)
      })
      .addCase(loginWithGoogle.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })

    // Sign out of all sessions → clear local auth
    builder.addCase(logoutAllSessions.fulfilled, (state) => {
      signOut(state)
    })

    // Sign out (server clears the cookie; local state cleared right away)
    builder.addCase(logout.pending, (state) => {
      signOut(state)
    })

    // Fetch current user
    builder
      .addCase(fetchCurrentUser.fulfilled, (state, action: PayloadAction<User>) => {
        signIn(state, action.payload)
      })
      .addCase(fetchCurrentUser.rejected, (state) => {
        // 401 or unreachable server: no confirmed session -> signed out (cookie, if any, stays server-side).
        signOut(state)
        state.sessionChecked = true
      })
  },
})

export const { sessionExpired, clearAuthError } = authSlice.actions
export default authSlice.reducer