// Pure helpers (no React, no JSON imports) so they can be unit-tested with plain node.
// NOTE: keep this file "erasable" TypeScript (no enums / parameter properties) and import
// sibling files with explicit .ts extensions - node --test loads it directly.

export type LanguageCode = 'mr' | 'hi' | 'en'

export interface LanguageInfo {
  code: LanguageCode
  /** Name written in its own script - what users should see in the switcher. */
  nativeName: string
  /** English name, for aria-labels / tooltips. */
  englishName: string
}

// Order matters: this is the order shown in the switcher.
export const LANGUAGES: readonly LanguageInfo[] = [
  { code: 'mr', nativeName: 'मराठी', englishName: 'Marathi' },
  { code: 'hi', nativeName: 'हिंदी', englishName: 'Hindi' },
  { code: 'en', nativeName: 'English', englishName: 'English' },
]

export const SUPPORTED_LANGUAGES: readonly LanguageCode[] = LANGUAGES.map((l) => l.code)
export const DEFAULT_LANGUAGE: LanguageCode = 'en'
export const LANGUAGE_STORAGE_KEY = 'sl_lang'

export function isSupportedLanguage(code: unknown): code is LanguageCode {
  return typeof code === 'string' && (SUPPORTED_LANGUAGES as readonly string[]).includes(code)
}

/** "hi-IN" -> "hi"; returns null if not one of the three supported languages. */
export function normalizeLanguage(raw: unknown): LanguageCode | null {
  if (typeof raw !== 'string') return null
  const base = raw.trim().toLowerCase().split(/[-_]/)[0]
  return isSupportedLanguage(base) ? base : null
}

export interface StorageLike {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
}

export function readStoredLanguage(storage?: StorageLike | null): LanguageCode | null {
  try {
    return normalizeLanguage(storage?.getItem(LANGUAGE_STORAGE_KEY))
  } catch {
    return null // storage blocked (private mode etc.)
  }
}

export function storeLanguage(code: LanguageCode, storage?: StorageLike | null): void {
  try {
    storage?.setItem(LANGUAGE_STORAGE_KEY, code)
  } catch {
    /* ignore: the choice just will not persist */
  }
}

/** Saved choice > first supported browser language > English. */
export function detectLanguage(
  storage?: StorageLike | null,
  browserLanguages: readonly string[] = [],
): LanguageCode {
  const saved = readStoredLanguage(storage)
  if (saved) return saved
  for (const raw of browserLanguages) {
    const match = normalizeLanguage(raw)
    if (match) return match
  }
  return DEFAULT_LANGUAGE
}

export function isIndicLanguage(code: string | undefined | null): boolean {
  return code === 'hi' || code === 'mr'
}

// ---- browser-bound convenience wrappers (all guarded) ----

export function getBrowserStorage(): StorageLike | null {
  try {
    return typeof window !== 'undefined' ? window.localStorage : null
  } catch {
    return null
  }
}

export function getBrowserLanguages(): string[] {
  if (typeof navigator === 'undefined') return []
  const list = navigator.languages && navigator.languages.length ? [...navigator.languages] : []
  if (navigator.language) list.push(navigator.language)
  return list
}

export function applyDocumentLanguage(code: string): void {
  if (typeof document !== 'undefined' && document.documentElement) {
    document.documentElement.lang = code
  }
}
