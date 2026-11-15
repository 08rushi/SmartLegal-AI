import i18next, { type i18n, type Resource } from 'i18next'
import { initReactI18next } from 'react-i18next'
import {
  DEFAULT_LANGUAGE,
  SUPPORTED_LANGUAGES,
  applyDocumentLanguage,
  detectLanguage,
  normalizeLanguage,
  storeLanguage,
  type StorageLike,
} from './languages.ts'

export interface CreateI18nOptions {
  storage?: StorageLike | null
  browserLanguages?: readonly string[]
  /** Register react-i18next (skip in plain-node tests). */
  react?: boolean
  /** Namespaces to register; defaults to every namespace present in `resources`. */
  namespaces?: readonly string[]
}

/**
 * Builds an i18next instance. Language = saved choice > browser > English.
 * Every language change is persisted and mirrored on <html lang>.
 */
export function createI18n(resources: Resource, opts: CreateI18nOptions = {}): i18n {
  const instance = i18next.createInstance()
  if (opts.react) instance.use(initReactI18next)

  const initial = detectLanguage(opts.storage, opts.browserLanguages)

  void instance.init({
    resources,
    lng: initial,
    fallbackLng: DEFAULT_LANGUAGE,
    supportedLngs: [...SUPPORTED_LANGUAGES],
    nonExplicitSupportedLngs: false,
    ns: [
      ...(opts.namespaces ?? new Set(Object.values(resources).flatMap((r) => Object.keys(r as object)))),
    ],
    defaultNS: 'common',
    interpolation: { escapeValue: false }, // React already escapes
    returnNull: false,
    initAsync: false,
    react: { useSuspense: false },
  })

  applyDocumentLanguage(initial)
  instance.on('languageChanged', (lng: string) => {
    const code = normalizeLanguage(lng)
    if (!code) return
    storeLanguage(code, opts.storage)
    applyDocumentLanguage(code)
  })
  return instance
}
