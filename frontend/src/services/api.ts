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

// ── Auth response interceptor: clear token & redirect on 401 ──────────────
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Only redirect if we had a token (avoid redirect loop on login page)
      const hadToken = !!localStorage.getItem('sl_token')
      localStorage.removeItem('sl_token')
      if (hadToken && !window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ── Google Sign-In helper ──────────────────────────────────────────────────
export async function googleSignIn(credential: string) {
  const response = await apiClient.post('/auth/google', { credential })
  return response.data
}