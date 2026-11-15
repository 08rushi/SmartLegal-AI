/**
 * Accessibility + shell tests (plain node, no DOM):
 * - dialog helpers (focus trap index math, scroll-lock counting)
 * - navigation model (original nav items, Services dropdown matching)
 * - static guards: every overlay uses ui/Modal, Layout has skip link/landmarks/language selector,
 *   tokens defined, reduced-motion respected.
 */
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { nextTrapIndex, lockScroll, unlockScroll, _scrollLockCount } from '../utils/dialogA11y.ts'
import { NAV_ITEMS, SERVICE_CARDS, isServicesActive } from '../config/navigation.ts'

const here = path.dirname(fileURLToPath(import.meta.url))
const src = path.resolve(here, '..')
const read = (rel) => fs.readFileSync(path.join(src, rel), 'utf8')
const walk = (dir) =>
  fs.readdirSync(dir, { withFileTypes: true }).flatMap((d) => {
    const p = path.join(dir, d.name)
    return d.isDirectory() ? walk(p) : [p]
  })

test('nextTrapIndex wraps forwards and backwards', () => {
  assert.equal(nextTrapIndex(0, 3, false), 1)
  assert.equal(nextTrapIndex(2, 3, false), 0)
  assert.equal(nextTrapIndex(0, 3, true), 2)
  assert.equal(nextTrapIndex(1, 3, true), 0)
  assert.equal(nextTrapIndex(-1, 3, false), 0) // focus outside -> first
  assert.equal(nextTrapIndex(-1, 3, true), 2)
  assert.equal(nextTrapIndex(0, 0, false), -1) // nothing focusable
  assert.equal(nextTrapIndex(0, 1, false), 0)
})

test('scroll lock is reference counted', () => {
  const doc = { body: { style: { overflow: 'auto' } } }
  lockScroll(doc)
  lockScroll(doc)
  assert.equal(doc.body.style.overflow, 'hidden')
  unlockScroll(doc)
  assert.equal(doc.body.style.overflow, 'hidden')
  unlockScroll(doc)
  assert.equal(doc.body.style.overflow, 'auto')
  unlockScroll(doc) // extra unlock is harmless
  assert.equal(_scrollLockCount(), 0)
})

test('navigation: original five links, Services dropdown entries, active matching', () => {
  assert.deepEqual(NAV_ITEMS.map((n) => n.to), ['/', '/upload', '/analysis', '/chat', '/knowledge-base'])
  assert.deepEqual(SERVICE_CARDS.map((c) => c.to), ['/legal-id', '/property-hub', '/business-hub', '/yojana', '/tracker', '/services'])
  for (const c of SERVICE_CARDS) assert.match(c.titleKey, /^nav:serviceCards\./)
  assert.equal(isServicesActive('/legal-id/passport'), true)
  assert.equal(isServicesActive('/property-hub'), true)
  assert.equal(isServicesActive('/services'), true)
  assert.equal(isServicesActive('/tracker'), true)
  assert.equal(isServicesActive('/upload'), false)
  assert.equal(isServicesActive('/'), false)
})

test('every fixed full-screen overlay goes through ui/Modal', () => {
  const offenders = []
  for (const f of walk(path.join(src, 'pages')).concat(walk(path.join(src, 'components')))) {
    if (!f.endsWith('.tsx') || f.endsWith(path.join('ui', 'Modal.tsx'))) continue
    if (/fixed inset-0/.test(fs.readFileSync(f, 'utf8'))) offenders.push(path.relative(src, f))
  }
  assert.deepEqual(offenders, [])
})

test('Modal declares dialog semantics and uses the focus-trap hook', () => {
  const m = read('components/ui/Modal.tsx')
  assert.match(m, /role="dialog"/)
  assert.match(m, /aria-modal="true"/)
  assert.match(m, /aria-labelledby/)
  assert.match(m, /useDialogA11y/)
  const h = read('hooks/useDialogA11y.ts')
  assert.match(h, /Escape/)
  assert.match(h, /lockScroll/)
  assert.match(h, /previous\.focus\(\)/) // restores focus
})

test('Layout: skip link, landmarks, Services dropdown, language selector, no bottom tab bar', () => {
  const l = read('components/Layout.tsx')
  assert.match(l, /className="skip-link"/)
  assert.match(l, /id="main-content"/)
  assert.match(l, /<header/)
  assert.match(l, /<main/)
  assert.match(l, /<footer/)
  assert.match(l, /<nav\s[^>]*aria-label/)
  assert.match(l, /LanguageSwitcher/)
  assert.match(l, /SERVICE_CARDS/)
  assert.equal(/fixed inset-x-3 bottom-3/.test(l), false, 'the redesign bottom tab bar is gone')
})

test('design tokens exist in css and tailwind (mapped to the glass theme); reduced motion honoured', () => {
  const css = read('index.css')
  for (const v of ['--c-canvas', '--c-surface', '--c-fg', '--c-accent', '--c-focus', '--c-danger', '--c-warn', '--c-ok']) {
    assert.ok(css.includes(v), `missing ${v}`)
  }
  assert.match(css, /prefers-reduced-motion: reduce/)
  assert.match(css, /:focus-visible/)
  assert.match(css, /backdrop-filter:\s*blur/, 'glass theme keeps the blur')
  assert.match(css, /\.skip-link/)
  const tw = fs.readFileSync(path.resolve(src, '..', 'tailwind.config.js'), 'utf8')
  assert.match(tw, /canvas:/)
  assert.match(tw, /'on-accent'/)
})

test('risk is never colour alone: RiskPill renders an icon and a word', () => {
  const r = read('components/ui/RiskPill.tsx')
  assert.match(r, /<Icon/)
  assert.match(r, /\{word\}/)
  for (const lvl of ['high', 'medium', 'low']) assert.match(r, new RegExp(`${lvl}: \\{`))
})
