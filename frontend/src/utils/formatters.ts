/**
 * Shared Formatting Helpers (SL-039). Dates/numbers follow the active UI language (mr-IN/hi-IN/en-IN).
 */
import i18n from '../i18n'
import { formatLocalDate, formatLocalNumber, localeTag } from './i18nHelpers'

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${formatLocalNumber(parseFloat((bytes / Math.pow(k, i)).toFixed(1)))} ${sizes[i]}`
}

export function formatDate(isoString: string | null | undefined): string {
  if (!isoString) return i18n.t('store:notAvailable')
  try {
    return formatLocalDate(isoString) || isoString
  } catch {
    return isoString
  }
}

export function formatRelativeTime(isoString: string): string {
  if (!isoString) return i18n.t('store:time.recently')
  try {
    const date = new Date(isoString)
    const now = new Date()
    const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (Number.isNaN(diffSeconds)) return i18n.t('store:time.recently')
    if (diffSeconds < 60) return i18n.t('store:time.justNow')
    const rtf = new Intl.RelativeTimeFormat(localeTag(), { numeric: 'always', style: 'short' })
    if (diffSeconds < 3600) return rtf.format(-Math.floor(diffSeconds / 60), 'minute')
    if (diffSeconds < 86400) return rtf.format(-Math.floor(diffSeconds / 3600), 'hour')
    return rtf.format(-Math.floor(diffSeconds / 86400), 'day')
  } catch {
    return i18n.t('store:time.recently')
  }
}

export function sanitizeErrorMessage(err: unknown): string {
  if (typeof err === 'string') return err
  if (err && typeof err === 'object') {
    const e = err as { response?: { data?: { detail?: string } }; message?: string }
    if (e.response?.data?.detail) return e.response.data.detail
    if (e.message) return e.message
  }
  return i18n.t('store:unexpected')
}
