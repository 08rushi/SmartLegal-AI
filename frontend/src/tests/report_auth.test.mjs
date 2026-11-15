/**
 * Tests for (1) the localized analysis report builders and (2) the cookie-only auth / download contract.
 * Plain node --test; the builders in utils/pdfReport.ts are pure so they run here with real locale JSON.
 */
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { createI18n } from '../i18n/setup.ts'
import { LANGUAGES } from '../i18n/languages.ts'
import { buildReportHtml, buildReportPdf, escapeHtml, reportCss, reportFileBase } from '../utils/pdfReport.ts'

const here = path.dirname(fileURLToPath(import.meta.url))
const srcDir = path.resolve(here, '..')
const localesDir = path.join(srcDir, 'i18n/locales')

function buildResources() {
  const res = {}
  for (const { code } of LANGUAGES) {
    res[code] = {}
    for (const f of fs.readdirSync(path.join(localesDir, code)).filter((n) => n.endsWith('.json'))) {
      res[code][f.replace(/\.json$/, '')] = JSON.parse(fs.readFileSync(path.join(localesDir, code, f), 'utf8'))
    }
  }
  return res
}

const storage = { getItem: () => null, setItem: () => {} }
const i18n = createI18n(buildResources(), { storage, browserLanguages: ['en'] })
const ctxFor = (lang, translated) => ({
  t: i18n.getFixedT(lang, 'analysis'),
  lang,
  dateText: '15 Nov 2026',
  languageName: LANGUAGES.find((l) => l.code === lang).nativeName,
  translated,
})

const analysis = (text) => ({
  document_id: 'd1',
  analyzed_at: '2026-11-15T00:00:00Z',
  summary: {
    document_type: text.type,
    total_clauses: 1,
    high_risk_count: 1,
    medium_risk_count: 0,
    low_risk_count: 0,
    overall_risk: 'high',
    risk_summary: text.summary,
    parties: [text.party],
    key_dates: [{ label: text.dateLabel, date: '01-04-2026' }],
    your_obligations: [text.obligation],
    other_party_rights: [],
    high_risk_clauses: [text.risk],
    beneficial_clauses: [],
  },
  clauses: [
    {
      id: 'c1',
      title: text.clauseTitle,
      original_text: 'The Lessee shall pay <b>rent</b>.',
      plain_english: text.plain,
      plain_hindi: '',
      risk_level: 'high',
      risk_score: 8,
      risk_reason: text.reason,
      clause_type: 'Rent',
    },
  ],
})

const MR = analysis({
  type: 'निवासी भाडेकरार',
  summary: 'जास्त धोक्याचे मुद्दे आढळले <script>alert(1)</script>',
  party: 'श्री. राजेश शर्मा',
  dateLabel: 'सुरुवातीची तारीख',
  obligation: 'दरमहा भाडे भरा.',
  risk: 'एकतर्फी भाडेवाढ',
  clauseTitle: 'भाड्याची रक्कम',
  plain: 'तुम्ही दरमहा ₹25,000 भाडे द्याल.',
  reason: 'भाडेवाढ बाजारापेक्षा जास्त आहे.',
})

test('Marathi report: labels from i18n, translated content, escaped, no English chrome', () => {
  const html = buildReportHtml(MR, 'rent.pdf', ctxFor('mr', true))
  assert.match(html, /कायदेशीर दस्तऐवज आढावा/) // title label (mr)
  assert.match(html, /कलमवार तपशील \(1 कलमे काढली\)/) // interpolated heading
  assert.match(html, /तुम्ही दरमहा ₹25,000 भाडे द्याल\./) // translated clause text
  assert.match(html, /एआयने मराठी मध्ये भाषांतर केले आहे|एआयने .* मध्ये भाषांतर/) // translated-by-AI note
  assert.doesNotMatch(html, /Plain Language Summary|Legal Document Review|Clause-by-Clause/)
  assert.doesNotMatch(html, /<script>/) // content is HTML-escaped
  assert.match(html, /&lt;script&gt;/)
  assert.match(html, /15 Nov 2026/)
})

test('Hindi report uses Hindi labels; css targets Noto Sans Devanagari and print-only display', () => {
  const html = buildReportHtml(MR, null, ctxFor('hi', true))
  assert.match(html, /कानूनी दस्तावेज़ समीक्षा/)
  assert.match(html, /जोखिम/)
  const css = reportCss()
  assert.match(css, /Noto Sans Devanagari/)
  assert.match(css, /@media print/)
  assert.match(css, /display: none !important/)
})

test('English report is generated with jsPDF from i18n labels (code path runs, produces a valid PDF)', async () => {
  const EN = analysis({
    type: 'Rental Agreement',
    summary: 'High risk flags found.',
    party: 'A. Sharma',
    dateLabel: 'Start',
    obligation: 'Pay rent monthly.',
    risk: 'Unilateral escalation',
    clauseTitle: 'Rent',
    plain: 'You pay monthly rent.',
    reason: 'Above market.',
  })
  const doc = await buildReportPdf(EN, 'rent.pdf', { ...ctxFor('en', false), translated: false })
  assert.ok(doc.getNumberOfPages() >= 1)
  const bytes = doc.output('arraybuffer')
  assert.ok(bytes.byteLength > 1500)
  assert.equal(new TextDecoder().decode(new Uint8Array(bytes).slice(0, 5)), '%PDF-')
  const raw = doc.output()
  assert.match(raw, /Legal Document Review/)
  assert.match(raw, /Page 1 of 1/)
})

test('helpers: escapeHtml and report file name', () => {
  assert.equal(escapeHtml(`<a href="x">&'`), '&lt;a href=&quot;x&quot;&gt;&amp;&#39;')
  assert.equal(reportFileBase(MR, 'My Lease (v2).pdf'), 'SmartLegal_Analysis_My_Lease__v2__pdf')
})

// ── cookie-only auth / download contract (source-level, the stores need Vite to import) ────────────────
const read = (rel) => fs.readFileSync(path.join(srcDir, rel), 'utf8')

test('api client: cookie credentials, no Bearer header, no token in localStorage', () => {
  const api = read('services/api.ts')
  assert.match(api, /withCredentials:\s*true/)
  assert.doesNotMatch(api, /Authorization/)
  assert.doesNotMatch(api, /localStorage\.getItem\('sl_token'\)/)
})

test('auth slice: never stores or reads the body token; restores session via /auth/me; logout hits /auth/logout', () => {
  const slice = read('store/authSlice.ts')
  assert.doesNotMatch(slice, /\.access_token/)
  assert.doesNotMatch(slice, /localStorage\.setItem/)
  assert.match(slice, /localStorage\.removeItem\('sl_token'\)/) // leftover cleanup only
  assert.match(slice, /apiClient\.get<User>\('\/auth\/me'\)/)
  assert.match(slice, /apiClient\.post\('\/auth\/logout'\)/)
  const app = read('App.tsx')
  assert.match(app, /dispatch\(fetchCurrentUser\(\)\)/)
})

test('documents: no file_url anywhere; downloads go through the authenticated download endpoint', () => {
  assert.doesNotMatch(read('types/index.ts'), /file_url/)
  assert.doesNotMatch(read('utils/demoData.ts'), /file_url/)
  assert.match(read('services/api.ts'), /\/upload\/\$\{encodeURIComponent\(documentId\)\}\/download/)
  assert.match(read('pages/MyDocuments.tsx'), /documentDownloadUrl\(doc\.id\)/)
})
