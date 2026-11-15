/**
 * Informational lint: finds obvious hardcoded user-visible English in JSX under src/pages and
 * src/components (JSX text nodes, and title/placeholder/aria-label/alt string-literal attributes).
 * Prints a per-file report. Strict by default: fails on any hit (I18N_STRICT=0 makes it informational).
 *
 * Heuristic only: it can over/under-count (e.g. brand names, symbols). Exported for reuse:
 *   import { scanAll, scanSource } from './hardcoded_text.test.mjs'
 */
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const srcDir = path.resolve(here, '..')
const SCAN_DIRS = ['pages', 'components']
// Strict by default (zero hardcoded strings enforced). Set I18N_STRICT=0 to downgrade to an informational report.
export const STRICT = process.env.I18N_STRICT !== '0'
// Brand names are intentionally not translated.
const BRAND_ALLOWLIST = new Set(['SmartLegal AI', 'SmartLegal'])

// Text nodes that are really JS code caught between a `)`/`(` of a ternary/switch/conditional expression.
function looksLikeCode(text) {
  if (/^\)|\($|^\?|&&|\breturn\b\s*\(?$|\bcase\s+['\"]|\bdefault:/.test(text)) return true
  if (/^&\s*\w+/.test(text)) return true // generic type intersection, e.g. "& ComponentPropsWithRef"
  if (/\.\w+\(/.test(text)) return true // method call such as t.includes('x')
  return false
}

// Text between a tag's '>' and the next '<', containing no code characters.
const TEXT_NODE = /(?<![=\-])>([^<>{}=;`]*?[A-Za-z]{2,}[^<>{}=;`]*?)</g
// Literal user-visible attributes, e.g. placeholder="Search" (not placeholder={t('x')}).
const ATTR = /\b(?:title|placeholder|aria-label|alt)=(?:"([^"]*[A-Za-z]{2,}[^"]*)"|'([^']*[A-Za-z]{2,}[^']*)')/g

function stripNoise(src) {
  return src
    .replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '))
    .replace(/(^|[^:])\/\/[^\n]*/g, (m, p) => p + ' '.repeat(m.length - p.length))
}

/** Returns [{line, text}] of suspected hardcoded strings in one source string. */
export function scanSource(src) {
  const clean = stripNoise(src)
  const hits = []
  const lineOf = (idx) => clean.slice(0, idx).split('\n').length
  for (const m of clean.matchAll(TEXT_NODE)) {
    const text = m[1].replace(/\s+/g, ' ').trim()
    if (!text || /^&\w+;$/.test(text)) continue
    if (BRAND_ALLOWLIST.has(text) || looksLikeCode(text)) continue
    // skip things that look like code / types rather than prose
    if (/^[\w.]+(\[\])?$/.test(text) && !/[A-Z][a-z]/.test(text) && text === text.toLowerCase()) continue
    if (/[()|&:]/.test(text) && !/\s/.test(text)) continue
    hits.push({ line: lineOf(m.index), text })
  }
  for (const m of clean.matchAll(ATTR)) {
    const attrText = (m[1] ?? m[2]).trim()
    if (BRAND_ALLOWLIST.has(attrText)) continue
    hits.push({ line: lineOf(m.index), text: attrText })
  }
  return hits
}

function walk(dir) {
  if (!fs.existsSync(dir)) return []
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((d) => {
    const p = path.join(dir, d.name)
    if (d.isDirectory()) return walk(p)
    return /\.tsx$/.test(d.name) ? [p] : []
  })
}

/** { files: {relPath: hits[]}, total } across src/pages and src/components. */
export function scanAll() {
  const files = {}
  let total = 0
  for (const d of SCAN_DIRS) {
    for (const f of walk(path.join(srcDir, d))) {
      const hits = scanSource(fs.readFileSync(f, 'utf8'))
      if (hits.length) {
        files[path.relative(srcDir, f).replace(/\\/g, '/')] = hits
        total += hits.length
      }
    }
  }
  return { files, total }
}

export const HARDCODED_TOTAL = scanAll().total

test('scanner detects obvious hardcoded JSX text and attributes', () => {
  const hits = scanSource('const A = () => (<div><h1>Hello world</h1><input placeholder="Search" aria-label={t("x")} /></div>)')
  assert.equal(hits.length, 2)
  assert.equal(scanSource('const A = () => <p>{t("home:title")}</p>').length, 0)
  // known false positives: code between JSX expressions, brand name
  assert.equal(scanSource("const A = () => (c ? (<b/>) : x ? (<i/>) : null)").length, 0)
  assert.equal(scanSource("switch (k) { case 'a': return (<g/>) }").length, 0)
  assert.equal(scanSource('const A = () => <img alt="SmartLegal AI" />').length, 0)
})

test('hardcoded-text report (informational)', () => {
  const { files, total } = scanAll()
  const rows = Object.entries(files)
    .map(([f, h]) => [f, h.length])
    .sort((a, b) => b[1] - a[1])
  console.log(`\n[i18n] hardcoded user-visible strings (heuristic): ${total} in ${rows.length} files`)
  for (const [f, n] of rows.slice(0, 30)) console.log(`  ${String(n).padStart(4)}  ${f}`)
  if (STRICT) assert.equal(total, 0, `${total} hardcoded strings remain`)
})
