import i18n from '../i18n'

interface ErrorLike {
  code?: string
  message?: string
  response?: { status?: number; data?: { detail?: unknown; error?: unknown } }
}

/**
 * User-facing message for a failed API call, in the ACTIVE language.
 * - A server-provided string `detail` is shown as-is (the backend translates it via X-Lang).
 * - FastAPI validation errors (list of {msg}) are joined into readable text.
 * - No HTTP response at all (server down / offline / CORS) -> translated network message.
 * - Anything else -> the translated generic fallback (an i18n key such as 'store:hub.typesFailed').
 */
export function apiErrorMessage(err: unknown, fallbackKey: string = 'store:generic'): string {
  const e = (err ?? {}) as ErrorLike
  const detail = e.response?.data?.detail ?? e.response?.data?.error
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail)) {
    const text = detail
      .map((d) => ((d as { msg?: string })?.msg || '').replace(/^Value error, /, ''))
      .filter(Boolean)
      .join(' ')
    if (text) return text
  }
  if (!e.response) return i18n.t('store:network')
  return i18n.t(fallbackKey)
}
