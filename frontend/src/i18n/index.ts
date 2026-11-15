import type { Resource } from 'i18next'
import { createI18n } from './setup'
import { getBrowserLanguages, getBrowserStorage } from './languages'

// All locale files are discovered automatically: src/i18n/locales/<lang>/<namespace>.json.
// To add a namespace: create <ns>.json in every language folder - no registration needed.
// To add a language: add a locales/<code>/ folder and register it in LANGUAGES (languages.ts).
// src/tests/i18n.test.mjs fails if any language has missing/extra/empty keys.
const modules = import.meta.glob('./locales/*/*.json', { eager: true, import: 'default' }) as Record<
  string,
  Record<string, unknown>
>

export const resources: Resource = {}
for (const [file, content] of Object.entries(modules)) {
  const m = file.match(/\.\/locales\/([^/]+)\/([^/]+)\.json$/)
  if (!m) continue
  const [, lang, ns] = m
  ;(resources[lang] ??= {})[ns] = content as Resource[string][string]
}

export const NAMESPACE_LIST = Array.from(new Set(Object.values(resources).flatMap((r) => Object.keys(r)))).sort()

// TODO(backend persistence, later task): when the profile API supports a language
// preference, read it after login and call i18n.changeLanguage(); write on change.
const i18n = createI18n(resources, {
  storage: getBrowserStorage(),
  browserLanguages: getBrowserLanguages(),
  react: true,
  namespaces: NAMESPACE_LIST,
})

export default i18n
