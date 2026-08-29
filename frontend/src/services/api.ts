import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 60000,
  headers: {
    Accept: 'application/json',
  },
})

// ── Auth request interceptor: attach JWT on every request ──────────────────
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('sl_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Auth response interceptor ──────────────────────────────────────────────
// Intentionally does NOT hard-redirect on 401. A full-page `window.location`
// redirect during a background call (e.g. history/checklist fetch) blows away
// app state and causes a jarring reload. Instead, thunks handle their own 401s,
// and session expiry is detected by fetchCurrentUser on load — which clears the
// Redux token so <ProtectedRoute> can redirect via the router. 401s from
// optional/anonymous calls are simply surfaced to the caller.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
)

// ── Google Sign-In helper ──────────────────────────────────────────────────
export async function googleSignIn(credential: string) {
  const response = await apiClient.post('/auth/google', { credential })
  return response.data
}