import i18n from '../i18n'
import { DEFAULT_LANGUAGE, normalizeLanguage } from '../i18n/languages'
import type { AnalysisResult, Clause, RiskLevel, UploadedDocument } from '../types'

/**
 * Demo content. All user-visible text lives in the `demo` locale namespace (en/hi/mr) so demo mode
 * follows the selected language. Only non-translatable structure (ids, scores, page numbers) and the
 * original contract wording (the "document's own text") are kept here.
 */

const DEMO_CLAUSES: Array<{
  id: string
  page: number
  risk: RiskLevel
  score: number
  originalText: string
}> = [
  {
    id: 'demo-clause-1',
    page: 1,
    risk: 'high',
    score: 8,
    originalText:
      'The Lessee shall pay a monthly rent of Rs. 25,000/-. Upon completion of 11 months, the monthly rent shall automatically escalate by 15% per annum for any extension period without requiring fresh consent.',
  },
  {
    id: 'demo-clause-2',
    page: 2,
    risk: 'high',
    score: 9,
    originalText:
      'The Lessee has deposited Rs. 75,000/- as interest-free security deposit. In the event the Lessee vacates the premises prior to the completion of the 11-month lock-in period, the entire security deposit shall stand forfeited to the Lessor.',
  },
  {
    id: 'demo-clause-3',
    page: 2,
    risk: 'medium',
    score: 6,
    originalText:
      'The Lessee shall bear costs for all minor day-to-day repairs up to Rs. 5,000 per occurrence. Major structural repairs shall be executed by the Lessor within reasonable time upon receiving notice.',
  },
  {
    id: 'demo-clause-4',
    page: 3,
    risk: 'medium',
    score: 5,
    originalText:
      'Subsequent to the lock-in period, either party may terminate this lease by issuing a 60-day prior written notice or paying rent in lieu thereof to the other party.',
  },
  {
    id: 'demo-clause-5',
    page: 3,
    risk: 'low',
    score: 2,
    originalText:
      'The Lessor or authorized representative may enter and inspect the premises during reasonable daylight hours after giving 24 hours advance notice to the Lessee.',
  },
  {
    id: 'demo-clause-6',
    page: 3,
    risk: 'low',
    score: 3,
    originalText:
      'The Lessee shall not sublet, assign, or part with possession of the premises nor make any structural alterations without prior written consent of the Lessor.',
  },
]

const ANALYZED_AT = new Date().toISOString()

export const demoDocument: UploadedDocument = {
  id: 'demo',
  filename: 'Sample_Residential_Rental_Agreement.pdf',
  file_size: 428500, // ~418 KB
  document_type: 'Residential Rental Agreement',
  uploaded_at: ANALYZED_AT,
  status: 'ready',
}

function resolveLang(lang?: string): string {
  return normalizeLanguage(lang ?? i18n.language) ?? DEFAULT_LANGUAGE
}

/** Demo document with its type label in the requested language (defaults to the active UI language). */
export function getDemoDocument(lang?: string): UploadedDocument {
  const t = i18n.getFixedT(resolveLang(lang), 'demo')
  return { ...demoDocument, document_type: t('documentType') }
}

type Fixed = ReturnType<typeof i18n.getFixedT>

function list(t: Fixed, key: string): string[] {
  const v = t(key, { returnObjects: true })
  return Array.isArray(v) ? (v as string[]) : []
}

/** Demo analysis in the requested language (defaults to the active UI language). */
export function getDemoAnalysisResult(lang?: string): AnalysisResult {
  const code = resolveLang(lang)
  const t = i18n.getFixedT(code, 'demo')
  const tHi = i18n.getFixedT('hi', 'demo')

  const keyDates = t('summary.keyDates', { returnObjects: true })
  const clauses: Clause[] = DEMO_CLAUSES.map((c, i) => ({
    id: c.id,
    title: t(`clauses.${i}.title`),
    clause_type: t(`clauses.${i}.type`),
    clause_number: t(`clauses.${i}.number`),
    page_number: c.page,
    risk_level: c.risk,
    risk_score: c.score,
    risk_reason: t(`clauses.${i}.reason`),
    // plain_english always holds the explanation in the *selected* language (same contract as the
    // backend's translated view); plain_hindi keeps the Hindi text for the English-mode toggle.
    plain_english: t(`clauses.${i}.plain`),
    plain_hindi: tHi(`clauses.${i}.plain`),
    original_text: c.originalText,
  }))

  return {
    document_id: 'demo',
    analyzed_at: ANALYZED_AT,
    summary: {
      document_type: t('summary.documentType'),
      total_clauses: clauses.length,
      high_risk_count: clauses.filter((c) => c.risk_level === 'high').length,
      medium_risk_count: clauses.filter((c) => c.risk_level === 'medium').length,
      low_risk_count: clauses.filter((c) => c.risk_level === 'low').length,
      overall_risk: 'high',
      risk_summary: t('summary.riskSummary'),
      high_risk_clauses: list(t, 'summary.highRiskClauses'),
      beneficial_clauses: list(t, 'summary.beneficialClauses'),
      your_obligations: list(t, 'summary.yourObligations'),
      other_party_rights: list(t, 'summary.otherPartyRights'),
      parties: list(t, 'summary.parties'),
      key_dates: Array.isArray(keyDates) ? (keyDates as { label: string; date: string }[]) : [],
    },
    clauses,
    view_lang: code,
  }
}

/** English demo analysis (kept for tests/back-compat). */
export const demoAnalysisResult: AnalysisResult = getDemoAnalysisResult('en')
