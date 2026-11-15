import axios from 'axios'
import i18n from '../i18n'
import { DEFAULT_LANGUAGE, normalizeLanguage } from '../i18n/languages'

/** Current UI language code ('en' | 'hi' | 'mr'). Safe to call anywhere. */
export function getCurrentLang(): string {
  return normalizeLanguage(i18n.language) ?? DEFAULT_LANGUAGE
}

// VITE_API_BASE_URL: unset -> local dev API; "/" or "same-origin" or "" -> same-origin requests
// (production behind the Vercel /api rewrite, so the session cookie stays first-party).
const RAW_BASE = import.meta.env.VITE_API_BASE_URL as string | undefined
const BASE_URL =
  RAW_BASE === undefined
    ? 'http://localhost:8000'
    : RAW_BASE === '/' || RAW_BASE === 'same-origin'
      ? ''
      : RAW_BASE.replace(/\/+$/, '')

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 60000,
  // Cookie-only auth: the HttpOnly `sl_token` cookie set by the backend carries the session.
  // No token is ever read from / written to JS-accessible storage.
  withCredentials: true,
  headers: {
    Accept: 'application/json',
  },
})

// ── Request interceptor: tell the backend which language to answer in ───────
apiClient.interceptors.request.use((config) => {
  config.headers['X-Lang'] = getCurrentLang()
  return config
})

/** Absolute API origin + /api/v1 (for plain navigations such as downloads). */
export const API_ROOT = `${BASE_URL}/api/v1`

/** URL of the authenticated download endpoint (redirects to a signed file URL). */
export function documentDownloadUrl(documentId: string): string {
  return `${API_ROOT}/upload/${encodeURIComponent(documentId)}/download`
}

// ── Auth response interceptor ──────────────────────────────────────────────
// Intentionally does NOT hard-redirect on 401. A full-page `window.location`
// redirect during a background call (e.g. history/checklist fetch) blows away
// app state and causes a jarring reload. Instead, thunks handle their own 401s,
// and session expiry is detected by fetchCurrentUser on load — which clears the
// Redux user so <ProtectedRoute> can redirect via the router. 401s from
// optional/anonymous calls are simply surfaced to the caller.
let unauthorizedHandler: (() => void) | null = null
/** Registered by the store: called when an authenticated (non-/auth/) request comes back 401. */
export function setUnauthorizedHandler(fn: (() => void) | null) {
  unauthorizedHandler = fn
}

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const url = String(error?.config?.url ?? '')
    if (status === 401 && unauthorizedHandler && !url.startsWith('/auth/')) {
      unauthorizedHandler() // clears local user state only; no redirect (see note above)
    }
    return Promise.reject(error)
  }
)

// ── Google Sign-In helper ──────────────────────────────────────────────────
export async function googleSignIn(credential: string) {
  const response = await apiClient.post('/auth/google', { credential })
  return response.data
}