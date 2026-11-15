/**
 * Locale-aware helpers shared by the document/analysis pages.
 * Numbers use Latin digits in every language (`-u-nu-latn`) so they match interpolated values.
 */
import type { TFunction } from 'i18next'
import i18n from '../i18n'

/** BCP-47 locale for Intl APIs. Without `lang` it follows the active UI language. */
export function localeTag(lang?: string): string {
  const base = String(lang || i18n.language || 'en').toLowerCase().slice(0, 2)
  if (base === 'mr') return 'mr-IN-u-nu-latn'
  if (base === 'hi') return 'hi-IN-u-nu-latn'
  return 'en-IN'
}

export function formatNumber(value: number, lang?: string, options?: Intl.NumberFormatOptions): string {
  try {
    return new Intl.NumberFormat(localeTag(lang), options).format(value)
  } catch {
    return String(value)
  }
}

export function formatPercent(ratio: number, lang?: string): string {
  return formatNumber(Math.round(ratio * 100), lang)
}

export function formatDateTime(iso: string, lang?: string, withTime = true): string {
  try {
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) return iso
    return new Intl.DateTimeFormat(localeTag(lang), {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      ...(withTime ? { hour: '2-digit', minute: '2-digit' } : {}),
    }).format(d)
  } catch {
    return iso
  }
}

function toDate(value: string | number | Date | null | undefined): Date | null {
  if (value === null || value === undefined || value === '') return null
  const d = value instanceof Date ? value : new Date(value)
  return Number.isNaN(d.getTime()) ? null : d
}

/** Localized date in the active (or given) language, e.g. "15 Nov 2026". '' for missing/invalid input. */
export function formatLocalDate(
  value: string | number | Date | null | undefined,
  options: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short', year: 'numeric' },
  lang?: string,
): string {
  const d = toDate(value)
  return d ? new Intl.DateTimeFormat(localeTag(lang), options).format(d) : ''
}

/** Localized time of day (hours and minutes). */
export function formatLocalTime(value: string | number | Date | null | undefined, lang?: string): string {
  const d = toDate(value)
  return d ? new Intl.DateTimeFormat(localeTag(lang), { hour: '2-digit', minute: '2-digit' }).format(d) : ''
}

/** Localized number in the active language (Latin digits). */
export function formatLocalNumber(value: number, options?: Intl.NumberFormatOptions): string {
  return formatNumber(value, undefined, options)
}

/** File size with translated unit labels (keys live in the `upload` namespace: units.byte/kb/mb). */
export function formatBytes(bytes: number, t: TFunction, lang?: string): string {
  if (!bytes || bytes < 0) return t('upload:units.byte', { value: formatNumber(0, lang) })
  if (bytes < 1024) return t('upload:units.byte', { value: formatNumber(bytes, lang) })
  if (bytes < 1024 * 1024) {
    return t('upload:units.kb', { value: formatNumber(bytes / 1024, lang, { maximumFractionDigits: 1, minimumFractionDigits: 1 }) })
  }
  return t('upload:units.mb', {
    value: formatNumber(bytes / (1024 * 1024), lang, { maximumFractionDigits: 1, minimumFractionDigits: 1 }),
  })
}

/** "Security Deposit" -> "security_deposit" (stable i18n key for free-form backend labels). */
export function enumSlug(raw: string): string {
  return raw
    .toLowerCase()
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9ऀ-ॿ]+/g, '_')
    .replace(/^_+|_+$/g, '')
}

/**
 * Translate a free-form backend label (risk level, clause type, document type, category ...)
 * via `<ns>:<group>.<slug>`; falls back to the raw value when no translation exists.
 */
export function enumLabel(t: TFunction, keyPrefix: string, raw: string | null | undefined): string {
  if (!raw) return ''
  const slug = enumSlug(raw)
  if (!slug) return raw
  return t(`${keyPrefix}.${slug}`, { defaultValue: raw })
}

/**
 * Map the well-known English fallback messages thrown by the store slices to translated text.
 * Anything else (e.g. a backend `detail`, already localized by X-Lang) is shown as returned.
 */
export function localizeKnownError(t: TFunction, message: string | null | undefined): string {
  if (!message) return ''
  const m = message.trim()
  const rules: Array<[RegExp, string]> = [
    [/^Upload failed\. Make sure the backend/i, 'docerrors:network'],
    [/^Upload failed$/i, 'docerrors:uploadFailed'],
    [/^Failed to load document history$/i, 'docerrors:history'],
    [/^Failed to delete the selected document/i, 'docerrors:delete'],
    [/^Failed to load document$/i, 'docerrors:load'],
    [/^Please sign in to use this feature/i, 'docerrors:signIn'],
    [/^Could not generate the .what if I sign. simulation/i, 'docerrors:consequences'],
    [/^Could not generate negotiation guidance/i, 'docerrors:negotiation'],
    [/^Could not generate the simulation/i, 'docerrors:consequences'],
    [/^Network Error$/i, 'docerrors:network'],
  ]
  for (const [re, key] of rules) {
    if (re.test(m)) return t(key)
  }
  return message
}
