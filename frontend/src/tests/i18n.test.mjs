/**
 * UXI-13 i18n tests (plain node --test, no DOM):
 * 1. en / hi / mr locale files have identical key sets per namespace, no empty values,
 *    and the same {{placeholders}} in every language.
 * 2. Language detection (saved > browser > English), switching, persistence across a
 *    simulated reload, <html lang> sync, and blocked-storage safety.
 * 3. Every namespace/resource registered in src/i18n/index.ts exists on disk.
 */
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import {
  LANGUAGES,
  LANGUAGE_STORAGE_KEY,
  detectLanguage,
  normalizeLanguage,
} from '../i18n/languages.ts'
import { createI18n } from '../i18n/setup.ts'

const here = path.dirname(fileURLToPath(import.meta.url))
const localesDir = path.resolve(here, '../i18n/locales')
const CODES = LANGUAGES.map((l) => l.code)
// Same discovery rule as src/i18n/index.ts (import.meta.glob './locales/*/*.json'):
// namespaces = every <ns>.json found under any language folder.
const NAMESPACES = [
  ...new Set(
    fs
      .readdirSync(localesDir, { withFileTypes: true })
      .filter((d) => d.isDirectory())
      .flatMap((d) => fs.readdirSync(path.join(localesDir, d.name)).filter((f) => f.endsWith('.json')))
      .map((f) => f.replace(/\.json$/, '')),
  ),
].sort()

function load(code, ns) {
  return JSON.parse(fs.readFileSync(path.join(localesDir, code, `${ns}.json`), 'utf8'))
}

function flatten(obj, prefix = '') {
  const out = {}
  for (const [k, v] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${k}` : k
    if (v && typeof v === 'object') Object.assign(out, flatten(v, key))
    else out[key] = v
  }
  return out
}

const placeholders = (s) => [...String(s).matchAll(/\{\{\s*(\w+)\s*\}\}/g)].map((m) => m[1]).sort().join(',')

function buildResources() {
  const res = {}
  for (const code of CODES) {
    res[code] = {}
    for (const ns of NAMESPACES) res[code][ns] = load(code, ns)
  }
  return res
}

function fakeStorage(initial = {}) {
  const data = { ...initial }
  return {
    data,
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => {
      data[k] = String(v)
    },
  }
}

test('supported languages are exactly mr, hi, en with native names', () => {
  assert.deepEqual(CODES.slice().sort(), ['en', 'hi', 'mr'])
  const names = Object.fromEntries(LANGUAGES.map((l) => [l.code, l.nativeName]))
  assert.equal(names.mr, 'मराठी')
  assert.equal(names.hi, 'हिंदी')
  assert.equal(names.en, 'English')
})

test('locale folders and namespaces are complete', () => {
  for (const code of CODES) {
    const files = fs.readdirSync(path.join(localesDir, code)).filter((f) => f.endsWith('.json')).sort()
    assert.deepEqual(files, NAMESPACES.map((n) => `${n}.json`).sort(), `${code}: files != NAMESPACES`)
  }
})

for (const ns of NAMESPACES) {
  test(`namespace "${ns}": identical key sets, no empty values, same placeholders`, () => {
    const flat = Object.fromEntries(CODES.map((c) => [c, flatten(load(c, ns))]))
    const baseKeys = Object.keys(flat.en).sort()
    for (const code of CODES) {
      assert.deepEqual(Object.keys(flat[code]).sort(), baseKeys, `${code}/${ns} key set differs from en`)
      for (const [k, v] of Object.entries(flat[code])) {
        assert.equal(typeof v, 'string', `${code}/${ns}.${k} must be a string`)
        assert.ok(v.trim().length > 0, `${code}/${ns}.${k} is empty`)
        assert.equal(placeholders(v), placeholders(flat.en[k]), `${code}/${ns}.${k} placeholders differ from en`)
      }
    }
  })
}

test('hi and mr values are really translated (contain Devanagari) except for brand/placeholder-only strings', () => {
  const devanagari = /[ऀ-ॿ]/
  for (const code of ['hi', 'mr']) {
    for (const ns of NAMESPACES) {
      for (const [k, v] of Object.entries(flatten(load(code, ns)))) {
        if (!devanagari.test(v)) {
          // only allowed: email example placeholder
          assert.equal(v, 'you@example.com', `${code}/${ns}.${k} is not translated: "${v}"`)
        }
      }
    }
  }
})

test('detectLanguage: saved choice > browser language > English', () => {
  assert.equal(detectLanguage(fakeStorage({ [LANGUAGE_STORAGE_KEY]: 'mr' }), ['hi-IN']), 'mr')
  assert.equal(detectLanguage(fakeStorage(), ['fr-FR', 'hi-IN', 'en']), 'hi')
  assert.equal(detectLanguage(fakeStorage(), ['mr']), 'mr')
  assert.equal(detectLanguage(fakeStorage(), ['fr-FR', 'ta']), 'en')
  assert.equal(detectLanguage(fakeStorage({ [LANGUAGE_STORAGE_KEY]: 'xx' }), []), 'en')
  assert.equal(detectLanguage(null, []), 'en')
  assert.equal(normalizeLanguage('MR_in'), 'mr')
  assert.equal(normalizeLanguage(undefined), null)
})

test('detectLanguage survives storage that throws', () => {
  const broken = {
    getItem() {
      throw new Error('blocked')
    },
    setItem() {
      throw new Error('blocked')
    },
  }
  assert.equal(detectLanguage(broken, ['hi']), 'hi')
})

test('switching language translates, persists, and survives a simulated reload', async () => {
  const storage = fakeStorage()
  const resources = buildResources()

  const first = createI18n(resources, { storage, browserLanguages: ['fr'] })
  assert.equal(first.language, 'en') // browser lang unsupported -> English
  assert.equal(first.t('nav:home'), 'Home')

  await first.changeLanguage('mr')
  assert.equal(first.language, 'mr')
  assert.equal(first.t('nav:home'), resources.mr.nav.home)
  assert.equal(storage.data[LANGUAGE_STORAGE_KEY], 'mr')

  await first.changeLanguage('hi')
  assert.equal(storage.data[LANGUAGE_STORAGE_KEY], 'hi')
  assert.equal(first.t('errors:notFound.title'), resources.hi.errors.notFound.title)

  // "reload": brand-new instance, same storage, different browser language
  const second = createI18n(resources, { storage, browserLanguages: ['en-US'] })
  assert.equal(second.language, 'hi')
  assert.equal(second.t('nav:login'), resources.hi.nav.login)
})

test('interpolation works in every language', () => {
  const resources = buildResources()
  for (const code of CODES) {
    const inst = createI18n(resources, { storage: fakeStorage({ [LANGUAGE_STORAGE_KEY]: code }) })
    assert.match(inst.t('footer:copyright', { year: 2031 }), /2031/)
    assert.match(inst.t('nav:signedInAs', { name: 'Asha' }), /Asha/)
  }
})

test('unsupported languages fall back to English; missing keys never crash', async () => {
  const inst = createI18n(buildResources(), { storage: fakeStorage() })
  await inst.changeLanguage('fr')
  assert.equal(inst.t('nav:home'), 'Home')
  assert.equal(inst.t('nav:doesNotExist'), 'doesNotExist')
})

test('browser-first load honours <html lang> sync when a document exists', async () => {
  const fakeDoc = { documentElement: { lang: 'en' } }
  globalThis.document = fakeDoc
  try {
    const inst = createI18n(buildResources(), { storage: fakeStorage(), browserLanguages: ['mr-IN'] })
    assert.equal(fakeDoc.documentElement.lang, 'mr')
    await inst.changeLanguage('hi')
    assert.equal(fakeDoc.documentElement.lang, 'hi')
  } finally {
    delete globalThis.document
  }
})

test('index.ts discovers locales with import.meta.glob (no per-file registration)', () => {
  const src = fs.readFileSync(path.resolve(here, '../i18n/index.ts'), 'utf8')
  assert.ok(src.includes("import.meta.glob('./locales/*/*.json'"), 'index.ts must glob locale files')
  assert.ok(NAMESPACES.length > 0)
})
