/**
 * Verdict / key risks / next steps / money-dates logic for the easy Analysis view (plain node --test).
 */
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { createI18n } from '../i18n/setup.ts'
import { LANGUAGES } from '../i18n/languages.ts'
import {
  computeVerdict,
  topRisks,
  nextSteps,
  moneyAndDates,
  firstSentence,
  buildVerdictView,
  isPartialResult,
} from '../utils/analysisVerdict.ts'
import { buildReportHtml } from '../utils/pdfReport.ts'

const clause = (id, risk_level, risk_score, extra = {}) => ({
  id,
  title: `Clause ${id}`,
  original_text: 'orig',
  plain_english: `Plain ${id}. More text.`,
  plain_hindi: '',
  risk_level,
  risk_score,
  risk_reason: 'why',
  clause_type: 'Rent',
  ...extra,
})

const result = (clauses, summary = {}, metadata) => ({
  document_id: 'd1',
  analyzed_at: '2026-11-15T00:00:00Z',
  clauses,
  metadata,
  summary: {
    document_type: 'Rental Agreement',
    parties: [],
    key_dates: [],
    overall_risk: 'low',
    risk_summary: 'summary',
    total_clauses: clauses.length,
    high_risk_count: clauses.filter((c) => c.risk_level === 'high').length,
    medium_risk_count: clauses.filter((c) => c.risk_level === 'medium').length,
    low_risk_count: clauses.filter((c) => c.risk_level === 'low').length,
    ...summary,
  },
})

test('verdict: overall high -> avoid (lawyer suggested)', () => {
  const v = computeVerdict(result([clause('1', 'high', 9)], { overall_risk: 'high' }))
  assert.equal(v.level, 'avoid')
  assert.equal(v.reason, 'overallHigh')
  assert.equal(v.suggestLawyer, true)
})

test('verdict: two high clauses -> avoid even if overall says medium', () => {
  const v = computeVerdict(result([clause('1', 'high', 8), clause('2', 'high', 7)], { overall_risk: 'medium' }))
  assert.equal(v.level, 'avoid')
  assert.equal(v.reason, 'manyHigh')
})

test('verdict: exactly one high clause with overall medium -> careful + lawyer', () => {
  const v = computeVerdict(result([clause('1', 'high', 8), clause('2', 'low', 2)], { overall_risk: 'medium' }))
  assert.equal(v.level, 'careful')
  assert.equal(v.reason, 'oneHigh')
  assert.equal(v.suggestLawyer, true)
})

test('verdict: overall medium or 3+ medium clauses -> careful; 2 medium + low overall -> safe', () => {
  assert.equal(computeVerdict(result([clause('1', 'medium', 5)], { overall_risk: 'medium' })).level, 'careful')
  const three = computeVerdict(result([clause('1', 'medium', 5), clause('2', 'medium', 5), clause('3', 'medium', 4)]))
  assert.equal(three.level, 'careful')
  assert.equal(three.reason, 'manyMedium')
  assert.equal(computeVerdict(result([clause('1', 'medium', 5), clause('2', 'medium', 4), clause('3', 'low', 1)])).level, 'safe')
})

test('verdict: low risk, no high clauses -> safe', () => {
  const v = computeVerdict(result([clause('1', 'low', 1), clause('2', 'low', 2)]))
  assert.equal(v.level, 'safe')
  assert.equal(v.suggestLawyer, false)
})

test('verdict: empty / missing data is never "safe"', () => {
  assert.equal(computeVerdict(null).level, 'careful')
  const v = computeVerdict(result([]))
  assert.equal(v.level, 'careful')
  assert.equal(v.reason, 'empty')
})

test('verdict: partial analysis is never "safe" but does not hide high risk', () => {
  const partial = result([clause('1', 'low', 1)], {}, { completion_ratio: 0.5 })
  assert.equal(isPartialResult(partial), true)
  const v = computeVerdict(partial)
  assert.equal(v.level, 'careful')
  assert.equal(v.reason, 'partial')
  assert.equal(computeVerdict(result([clause('1', 'high', 9)], { overall_risk: 'high', is_partial: true })).level, 'avoid')
})

test('verdict: falls back to summary counts when the clause list is empty', () => {
  const r = result([], { total_clauses: 5, high_risk_count: 2, medium_risk_count: 1, low_risk_count: 2 })
  assert.equal(computeVerdict(r).level, 'avoid')
})

test('topRisks: high before medium, by score, max 3, never low', () => {
  const list = [clause('a', 'low', 1), clause('b', 'medium', 6), clause('c', 'high', 7), clause('d', 'high', 9), clause('e', 'medium', 8)]
  const top = topRisks(list)
  assert.deepEqual(top.map((r) => r.clause.id), ['d', 'c', 'e'])
  assert.equal(top[0].index, 3)
  assert.deepEqual(topRisks([clause('a', 'low', 1)]), [])
  assert.deepEqual(topRisks(undefined), [])
})

test('firstSentence trims to one sentence and handles Devanagari danda', () => {
  assert.equal(firstSentence('You pay rent. You also pay tax.'), 'You pay rent.')
  assert.equal(firstSentence('तुम्ही भाडे द्याल। दुसरे वाक्य।'), 'तुम्ही भाडे द्याल।')
  assert.equal(firstSentence(''), '')
  assert.ok(firstSentence('x'.repeat(500)).length <= 220)
})

test('nextSteps: high risk, obligations and dates give at most 3 concrete steps', () => {
  const r = result([clause('1', 'high', 9), clause('2', 'high', 8)], {
    overall_risk: 'high',
    your_obligations: ['Pay rent monthly. Keep the flat clean.'],
    key_dates: [{ label: 'Start', date: '01-04-2026' }],
  })
  const steps = nextSteps(r)
  assert.equal(steps.length, 3)
  assert.equal(steps[0].key, 'askChange')
  assert.equal(steps[0].params.count, 2)
  assert.equal(steps[0].params.title, 'Clause 1')
  assert.equal(steps[1].key, 'obligation')
  assert.equal(steps[1].params.item, 'Pay rent monthly.')
  assert.equal(steps[2].key, 'date')
})

test('nextSteps: medium-only doc asks to read the careful clauses; missing data gives fewer steps', () => {
  const steps = nextSteps(result([clause('1', 'medium', 5), clause('2', 'medium', 4)]))
  assert.deepEqual(steps.map((s) => s.key), ['readMedium'])
  assert.equal(steps[0].params.count, 2)
  assert.deepEqual(nextSteps(result([clause('1', 'low', 1)])), [])
  assert.deepEqual(nextSteps(null), [])
})

test('nextSteps: partial / unclear text adds the "check the original" step', () => {
  assert.ok(nextSteps(result([clause('1', 'low', 1)], {}, { completion_ratio: 0.4 })).some((s) => s.key === 'checkMissing'))
  assert.ok(nextSteps(result([clause('1', 'low', 1, { is_unclear: true })])).some((s) => s.key === 'checkMissing'))
})

test('moneyAndDates extracts amounts and flags notice periods; empty when nothing present', () => {
  const r = result([], {
    key_dates: [
      { label: 'Notice period', date: '2 months' },
      { label: 'Rent due', date: '5th of month' },
    ],
    your_obligations: ['Pay ₹25,000 rent and Rs. 50,000 deposit', 'Pay ₹25,000 again'],
  })
  const md = moneyAndDates(r)
  assert.deepEqual(md.amounts, ['₹25,000', 'Rs. 50,000'])
  assert.equal(md.dates.length, 2)
  assert.equal(md.dates[0].notice, true)
  assert.equal(md.dates[1].notice, false)
  assert.deepEqual(moneyAndDates(result([])), { amounts: [], dates: [] })
  assert.deepEqual(moneyAndDates(null), { amounts: [], dates: [] })
})

// ---- real locale texts -------------------------------------------------------------------------

const localesDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../i18n/locales')
const res = {}
for (const { code } of LANGUAGES) {
  res[code] = {}
  for (const f of fs.readdirSync(path.join(localesDir, code)).filter((n) => n.endsWith('.json'))) {
    res[code][f.replace(/\.json$/, '')] = JSON.parse(fs.readFileSync(path.join(localesDir, code, f), 'utf8'))
  }
}
const i18n = createI18n(res, { storage: { getItem: () => null, setItem: () => {} }, browserLanguages: ['en'] })

const risky = result([clause('1', 'high', 9), clause('2', 'medium', 5)], {
  overall_risk: 'high',
  your_obligations: ['Pay rent monthly.'],
})

test('buildVerdictView builds translated texts in en / hi / mr with interpolation', () => {
  const en = buildVerdictView(risky, i18n.getFixedT('en', 'analysis'), 'Rental Agreement')
  assert.equal(en.levelText, 'Do not sign yet')
  assert.equal(en.risks.length, 2)
  assert.match(en.steps[0], /Clause 1/)
  assert.match(en.speech, /Do not sign yet/)
  assert.match(en.speech, /What to do next/)
  assert.doesNotMatch(en.speech, /\{\{|verdict:/)
  for (const code of ['hi', 'mr']) {
    const v = buildVerdictView(risky, i18n.getFixedT(code, 'analysis'), 'X')
    assert.notEqual(v.levelText, en.levelText)
    assert.match(v.steps[0], /Clause 1/)
    assert.match(v.speech, /[ऀ-ॿ]/)
    assert.doesNotMatch(v.speech, /\{\{|verdict:/)
  }
})

test('print report starts with verdict, key risks and next steps', () => {
  const ctx = { t: i18n.getFixedT('en', 'analysis'), lang: 'en', dateText: 'x', languageName: 'English', translated: false }
  const html = buildReportHtml(risky, 'a.pdf', ctx)
  const glance = html.indexOf('Result at a glance')
  assert.ok(glance > 0)
  assert.ok(html.indexOf('Do not sign yet') > glance)
  assert.ok(html.indexOf('Main risks') > glance)
  assert.ok(html.indexOf('What to do next') > glance)
  assert.ok(glance < html.indexOf('Key Contract Details') || html.indexOf('Key Contract Details') === -1)
  assert.ok(glance < html.indexOf('Clause-by-Clause'))
})

test('Analysis page order: verdict, key risks, next steps, full clauses, then details (no Simple/Details toggle)', async () => {
  const fs = await import('node:fs')
  const src = fs.readFileSync(new URL('../pages/Analysis.tsx', import.meta.url), 'utf8')
  const at = (needle) => {
    const i = src.indexOf(needle)
    assert.ok(i > 0, `missing ${needle}`)
    return i
  }
  const order = [
    '<VerdictCard',
    '<KeyRisks',
    '<NextSteps',
    'aria-labelledby="clauses-heading"',
    'aria-labelledby="summary-heading"',
    'aria-labelledby="overview-heading"',
    'aria-labelledby="consequences-heading"',
  ].map(at)
  assert.deepEqual(order, [...order].sort((a, b) => a - b))
  assert.equal(src.includes('sl_analysis_mode'), false)
  assert.equal(src.includes('verdict:mode'), false)
})
