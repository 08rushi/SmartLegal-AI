/**
 * Pure logic for the "easy" analysis view: traffic-light verdict, top risks, next steps, money and dates.
 * No React / i18n imports so it runs under plain `node --test` (src/tests/analysis_verdict.test.mjs).
 *
 * Everything is derived on the client from fields the analysis already has. Nothing here invents law:
 * the texts come from i18n keys (`verdict:*`) with interpolation, so they translate to hi / mr.
 *
 * VERDICT RULES (first match wins):
 *   avoid   ("Do not sign yet")  overall_risk is "high"  OR  2 or more high-risk clauses
 *   careful ("Read carefully")   exactly 1 high-risk clause  OR  overall_risk "medium"  OR  3 or more
 *                                medium-risk clauses  OR  partial analysis  OR  no clauses at all
 *   safe    ("Safe to sign")     everything else (overall low, no high clauses, at most 2 medium)
 * A partial analysis can never be "safe", and a document with no clauses is never "safe".
 */
import type { AnalysisResult, Clause } from '../types'

export type VerdictLevel = 'safe' | 'careful' | 'avoid'
export type VerdictReason = 'overallHigh' | 'manyHigh' | 'oneHigh' | 'overallMedium' | 'manyMedium' | 'partial' | 'empty' | 'low'

export type VerdictT = (key: string, options?: Record<string, unknown>) => string

export interface Verdict {
  level: VerdictLevel
  reason: VerdictReason
  highCount: number
  mediumCount: number
  partial: boolean
  /** Show the "talk to a lawyer" button. */
  suggestLawyer: boolean
}

const RANK: Record<string, number> = { high: 3, medium: 2, low: 1 }

export function isPartialResult(result: AnalysisResult | null | undefined): boolean {
  if (!result) return false
  const m = result.metadata
  return (
    result.summary?.is_partial === true ||
    (m?.completion_ratio != null && m.completion_ratio < 1) ||
    Boolean(m?.incomplete_chunks && m.incomplete_chunks.length > 0)
  )
}

function counts(result: AnalysisResult): { high: number; medium: number; total: number } {
  const clauses = result.clauses ?? []
  if (clauses.length > 0) {
    return {
      high: clauses.filter((c) => c.risk_level === 'high').length,
      medium: clauses.filter((c) => c.risk_level === 'medium').length,
      total: clauses.length,
    }
  }
  const s = result.summary
  const high = Number(s?.high_risk_count) || 0
  const medium = Number(s?.medium_risk_count) || 0
  return { high, medium, total: Number(s?.total_clauses) || high + medium + (Number(s?.low_risk_count) || 0) }
}

export function computeVerdict(result: AnalysisResult | null | undefined): Verdict {
  if (!result) {
    return { level: 'careful', reason: 'empty', highCount: 0, mediumCount: 0, partial: false, suggestLawyer: false }
  }
  const { high, medium, total } = counts(result)
  const partial = isPartialResult(result)
  const overall = result.summary?.overall_risk
  const base = { highCount: high, mediumCount: medium, partial }

  if (overall === 'high') return { ...base, level: 'avoid', reason: 'overallHigh', suggestLawyer: true }
  if (high >= 2) return { ...base, level: 'avoid', reason: 'manyHigh', suggestLawyer: true }
  if (high === 1) return { ...base, level: 'careful', reason: 'oneHigh', suggestLawyer: true }
  if (partial) return { ...base, level: 'careful', reason: 'partial', suggestLawyer: false }
  if (total === 0) return { ...base, level: 'careful', reason: 'empty', suggestLawyer: false }
  if (overall === 'medium') return { ...base, level: 'careful', reason: 'overallMedium', suggestLawyer: false }
  if (medium >= 3) return { ...base, level: 'careful', reason: 'manyMedium', suggestLawyer: false }
  return { ...base, level: 'safe', reason: 'low', suggestLawyer: false }
}

/** Which sentence key to show under the verdict word. */
export function verdictSentenceKey(v: Verdict): string {
  if (v.level === 'safe') return 'safe'
  if (v.reason === 'partial') return 'partial'
  if (v.reason === 'empty') return 'empty'
  return v.level
}

export interface KeyRisk {
  clause: Clause
  /** Index in the original clause list (for the "see full clause" jump). */
  index: number
}

/** Top `limit` clauses by risk (high before medium, then higher score first). Low-risk clauses are never listed. */
export function topRisks(clauses: Clause[] | undefined, limit = 3): KeyRisk[] {
  return (clauses ?? [])
    .map((clause, index) => ({ clause, index }))
    .filter(({ clause }) => clause.risk_level === 'high' || clause.risk_level === 'medium')
    .sort(
      (a, b) =>
        (RANK[b.clause.risk_level] ?? 0) - (RANK[a.clause.risk_level] ?? 0) ||
        (Number(b.clause.risk_score) || 0) - (Number(a.clause.risk_score) || 0) ||
        a.index - b.index,
    )
    .slice(0, limit)
}

/** One-sentence plain explanation: the plain-language text trimmed to its first sentence. */
export function firstSentence(text: string | undefined | null, max = 220): string {
  const s = String(text ?? '').replace(/\[UNCLEAR\]/g, '').replace(/\s+/g, ' ').trim()
  if (!s) return ''
  const m = s.match(/^.*?[.!?।॥](?=\s|$)/)
  let out = m ? m[0] : s
  if (out.length > max) out = `${out.slice(0, max - 1).trimEnd()}…`
  return out
}

export interface NextStep {
  /** Key under `verdict:steps.*` */
  key: 'askChange' | 'checkMissing' | 'readMedium' | 'obligation' | 'date'
  params: Record<string, unknown>
}

const hasUnclear = (c: Clause) =>
  Boolean(c.is_unclear) || Boolean(c.original_text?.includes('[UNCLEAR]')) || Boolean(c.plain_english?.includes('[UNCLEAR]'))

/** Up to `limit` concrete next steps, from data that exists. Fewer (or none) when data is missing. */
export function nextSteps(result: AnalysisResult | null | undefined, limit = 3): NextStep[] {
  if (!result) return []
  const steps: NextStep[] = []
  const clauses = result.clauses ?? []
  const highs = topRisks(clauses, 99).filter((r) => r.clause.risk_level === 'high')
  const { high, medium } = counts(result)
  const s = result.summary

  if (highs.length > 0) {
    steps.push({ key: 'askChange', params: { count: highs.length, title: highs[0].clause.title } })
  } else if (high > 0 && s?.high_risk_clauses?.[0]) {
    steps.push({ key: 'askChange', params: { count: high, title: s.high_risk_clauses[0] } })
  }
  if (isPartialResult(result) || clauses.some(hasUnclear)) steps.push({ key: 'checkMissing', params: {} })
  if (high === 0 && medium > 0) steps.push({ key: 'readMedium', params: { count: medium } })
  const obligation = (s?.your_obligations ?? []).find((o) => String(o ?? '').trim())
  if (obligation) steps.push({ key: 'obligation', params: { item: firstSentence(obligation, 200) } })
  const date = (s?.key_dates ?? []).find((d) => d && String(d.date ?? '').trim())
  if (date) steps.push({ key: 'date', params: { label: date.label, date: date.date } })
  return steps.slice(0, limit)
}

export interface MoneyDates {
  amounts: string[]
  dates: { label: string; date: string; notice: boolean }[]
}

const AMOUNT_RE = /(?:₹|Rs\.?|INR)\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:lakhs?|crores?|लाख|करोड़|कोटी))?/gi
const NOTICE_RE = /notice|नोटिस|सूचना|सूचन/i

/** Amounts (currency-looking text) and dates already present in the extracted summary. */
export function moneyAndDates(result: AnalysisResult | null | undefined): MoneyDates {
  const s = result?.summary
  if (!s) return { amounts: [], dates: [] }
  const dates = (s.key_dates ?? [])
    .filter((d) => d && (String(d.date ?? '').trim() || String(d.label ?? '').trim()))
    .map((d) => ({ label: String(d.label ?? ''), date: String(d.date ?? ''), notice: NOTICE_RE.test(String(d.label ?? '')) }))
  const sources = [...(s.your_obligations ?? []), ...(s.key_dates ?? []).map((d) => `${d?.label ?? ''} ${d?.date ?? ''}`), s.risk_summary ?? '']
  const seen = new Set<string>()
  const amounts: string[] = []
  for (const src of sources) {
    for (const m of String(src).matchAll(AMOUNT_RE)) {
      const v = m[0].replace(/\s+/g, ' ').trim().replace(/[.,]$/, '')
      if (!seen.has(v)) {
        seen.add(v)
        amounts.push(v)
      }
    }
  }
  return { amounts: amounts.slice(0, 6), dates }
}

// ---------------------------------------------------------------------------------------------
// Text assembly (shared by the page, the speaker and the PDF/print report)
// ---------------------------------------------------------------------------------------------

export interface VerdictView {
  verdict: Verdict
  levelText: string
  sentence: string
  docType: string
  risks: { title: string; text: string; riskLevel: string; index: number; score: number }[]
  steps: string[]
  /** Full text read aloud by the verdict speaker. */
  speech: string
}

/**
 * Builds all verdict texts. `t` may be any i18next `t` (keys carry the `verdict:` namespace prefix).
 * `docTypeLabel` is the already-localised document type (or '').
 */
export function buildVerdictView(result: AnalysisResult, t: VerdictT, docTypeLabel = ''): VerdictView {
  const verdict = computeVerdict(result)
  const levelText = t(`verdict:level.${verdict.level}`)
  const sentence = t(`verdict:sentence.${verdictSentenceKey(verdict)}`)
  const risks = topRisks(result.clauses, 3).map(({ clause, index }) => ({
    title: clause.title,
    text: firstSentence(clause.plain_english) || firstSentence(clause.risk_reason),
    riskLevel: clause.risk_level,
    index,
    score: clause.risk_score,
  }))
  const steps = nextSteps(result, 3).map((s) => t(`verdict:steps.${s.key}`, s.params))

  const parts: string[] = []
  if (docTypeLabel) parts.push(t('verdict:speech.docType', { type: docTypeLabel }))
  parts.push(levelText, sentence)
  if (risks.length) {
    parts.push(t('verdict:speech.risksHeading', { count: risks.length }))
    risks.forEach((r, i) => parts.push(`${i + 1}. ${r.title}`, r.text))
  }
  if (steps.length) {
    parts.push(t('verdict:speech.stepsHeading'))
    steps.forEach((s, i) => parts.push(`${i + 1}. ${s}`))
  }
  return { verdict, levelText, sentence, docType: docTypeLabel, risks, steps, speech: parts.filter(Boolean).join('\n') }
}
