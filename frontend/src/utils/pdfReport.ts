/**
 * Pure report builders (no i18n / app imports, so they run in node tests too).
 *
 * Two renderers share the same labels and content:
 *  - buildReportPdf():  jsPDF document for Latin-script (English). Direct file download.
 *  - buildReportHtml(): printable HTML for Devanagari (Hindi / Marathi). jsPDF has no text shaping
 *    (conjuncts / matras render broken with any embedded TTF), so the browser's own shaping engine
 *    renders the report (Noto Sans Devanagari is already bundled) and the user saves it as PDF
 *    from the print dialog.
 */
import type { AnalysisResult } from '../types'
import { buildVerdictView } from './analysisVerdict.ts'

export type ReportT = (key: string, options?: Record<string, unknown>) => string

export interface ReportContext {
  /** Translator bound to the report language and the `analysis` namespace (keys under `pdf.*`). */
  t: ReportT
  /** hi | mr | en */
  lang: string
  /** Localized "today" string shown in the header. */
  dateText: string
  /** Display name of the report language, e.g. "मराठी" (used in the "translated by AI" note). */
  languageName: string
  /** Whether the content is an AI translation of the base analysis. */
  translated: boolean
}

export function escapeHtml(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export function reportFileBase(result: AnalysisResult, filename?: string | null): string {
  const raw = filename || result.summary.document_type || 'Legal_Analysis'
  return `SmartLegal_Analysis_${raw.replace(/[^a-zA-Z0-9_-]/g, '_')}`
}

const RISK_COLORS: Record<string, { bg: string; fg: string }> = {
  high: { bg: '#fb7185', fg: '#e11d48' },
  medium: { bg: '#f5c26b', fg: '#b45309' },
  low: { bg: '#34d399', fg: '#059669' },
}

const VERDICT_COLORS: Record<string, { fg: string; rgb: [number, number, number] }> = {
  safe: { fg: '#047857', rgb: [4, 120, 87] },
  careful: { fg: '#b45309', rgb: [180, 83, 9] },
  avoid: { fg: '#be123c', rgb: [190, 18, 60] },
}

// ─────────────────────────────────────────────────────────────────────────────
// HTML (print) renderer: Devanagari-safe
// ─────────────────────────────────────────────────────────────────────────────

export const PRINT_ROOT_ID = 'sl-print-root'

export function reportCss(): string {
  return `
@media screen { #${PRINT_ROOT_ID} { display: none !important; } }
@media print {
  @page { size: A4; margin: 14mm 13mm 16mm 13mm; }
  html, body { background: #ffffff !important; }
  body > *:not(#${PRINT_ROOT_ID}) { display: none !important; }
  #${PRINT_ROOT_ID} { display: block !important; position: static; }
}
#${PRINT_ROOT_ID} {
  font-family: 'Noto Sans Devanagari', 'Inter', system-ui, sans-serif;
  color: #0f172a; background: #ffffff; font-size: 11pt; line-height: 1.65;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
#${PRINT_ROOT_ID} * { box-sizing: border-box; }
#${PRINT_ROOT_ID} .r-bar { background: #0f172a; color: #f5c26b; padding: 6px 10px; font-size: 9pt; font-weight: 700; display: flex; justify-content: space-between; border-radius: 4px; }
#${PRINT_ROOT_ID} .r-bar span:last-child { color: #fff; font-weight: 400; }
#${PRINT_ROOT_ID} h1 { font-size: 20pt; margin: 14px 0 2px; font-weight: 700; }
#${PRINT_ROOT_ID} h2 { font-size: 13pt; margin: 16px 0 6px; font-weight: 700; break-after: avoid; }
#${PRINT_ROOT_ID} .r-file { color: #64748b; font-size: 10pt; margin-bottom: 10px; }
#${PRINT_ROOT_ID} .r-note { color: #475569; font-size: 9pt; border-left: 3px solid #f5c26b; padding: 2px 8px; margin: 6px 0 10px; }
#${PRINT_ROOT_ID} .r-card { border: 1px solid #e2e8f0; background: #f8fafc; border-radius: 8px; padding: 10px 12px; break-inside: avoid; }
#${PRINT_ROOT_ID} .r-stats { display: flex; flex-wrap: wrap; gap: 6px 18px; align-items: center; font-weight: 700; font-size: 10pt; margin-bottom: 6px; }
#${PRINT_ROOT_ID} .r-badge { color: #0f172a; border-radius: 4px; padding: 1px 10px; font-size: 9pt; font-weight: 700; }
#${PRINT_ROOT_ID} ul { margin: 4px 0 8px 18px; padding: 0; }
#${PRINT_ROOT_ID} li { margin-bottom: 3px; }
#${PRINT_ROOT_ID} .r-label { font-weight: 700; }
#${PRINT_ROOT_ID} .r-verdict { font-size: 20pt; font-weight: 800; line-height: 1.3; }
#${PRINT_ROOT_ID} ol { margin: 4px 0 8px 20px; padding: 0; }
#${PRINT_ROOT_ID} .r-clause { border-bottom: 1px solid #e2e8f0; padding: 8px 0 10px; break-inside: avoid; }
#${PRINT_ROOT_ID} .r-clause-head { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }
#${PRINT_ROOT_ID} .r-clause-title { font-weight: 700; font-size: 11pt; }
#${PRINT_ROOT_ID} .r-risk { font-weight: 700; font-size: 9pt; white-space: nowrap; }
#${PRINT_ROOT_ID} .r-sub { font-weight: 700; font-size: 9pt; color: #334155; margin-top: 4px; }
#${PRINT_ROOT_ID} .r-warn { font-weight: 700; font-size: 9pt; color: #e11d48; margin-top: 4px; }
#${PRINT_ROOT_ID} .r-text { font-size: 10pt; color: #1e293b; white-space: pre-wrap; }
#${PRINT_ROOT_ID} .r-orig { font-size: 8.5pt; color: #64748b; white-space: pre-wrap; }
#${PRINT_ROOT_ID} .r-foot { margin-top: 16px; font-size: 8.5pt; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 6px; font-style: italic; }
#${PRINT_ROOT_ID} .r-wm { position: fixed; left: 0; right: 0; top: 42%; text-align: center; transform: rotate(-35deg); font-size: 40pt; font-weight: 800; color: #94a3b8; opacity: 0.14; pointer-events: none; z-index: 0; line-height: 1.2; }
#${PRINT_ROOT_ID} .r-wm small { display: block; font-size: 20pt; }
#${PRINT_ROOT_ID} .r-body { position: relative; z-index: 1; }
`
}

function list(items: string[] | undefined): string {
  const rows = (items ?? []).filter(Boolean)
  return rows.length ? `<ul>${rows.map((i) => `<li>${escapeHtml(i)}</li>`).join('')}</ul>` : ''
}

/** Self-contained printable report body (markup only; pair with reportCss()). */
export function buildReportHtml(result: AnalysisResult, filename: string | null | undefined, ctx: ReportContext): string {
  const { t } = ctx
  const s = result.summary
  const level = (r: string) => t(`pdf.risk.${r}`, { defaultValue: r })
  const colors = RISK_COLORS[s.overall_risk] ?? RISK_COLORS.medium

  const parts: string[] = []
  parts.push(`<div class="r-wm" aria-hidden="true">SMARTLEGAL AI<small>${escapeHtml(t('pdf.watermarkSub'))}</small></div>`)
  parts.push('<div class="r-body">')
  parts.push(
    `<div class="r-bar"><span>${escapeHtml(t('pdf.reportHeader'))}</span><span>${escapeHtml(ctx.dateText)}</span></div>`,
  )
  parts.push(`<h1>${escapeHtml(t('pdf.title'))}</h1>`)
  parts.push(
    `<div class="r-file">${escapeHtml(t('pdf.file', { name: filename || s.document_type || '—' }))}</div>`,
  )
  if (ctx.translated) {
    parts.push(`<div class="r-note">${escapeHtml(t('pdf.translatedNote', { language: ctx.languageName }))}</div>`)
  }

  // Result at a glance: verdict, main risks, next steps (same logic and texts as the Analysis page).
  const view = buildVerdictView(result, t)
  const vc = VERDICT_COLORS[view.verdict.level]
  parts.push(`<h2>${escapeHtml(t('verdict:pdf.glance'))}</h2>`)
  parts.push(
    `<div class="r-card" style="border:2px solid ${vc.fg}"><div class="r-verdict" style="color:${vc.fg}">${escapeHtml(view.levelText)}</div>` +
      `<div class="r-text">${escapeHtml(view.sentence)}</div></div>`,
  )
  if (view.risks.length) {
    parts.push(`<h2>${escapeHtml(t('verdict:pdf.risks'))}</h2><ol>`)
    view.risks.forEach((r) => {
      const rc = RISK_COLORS[r.riskLevel] ?? RISK_COLORS.medium
      parts.push(
        `<li><span class="r-label">${escapeHtml(r.title)}</span> <span class="r-risk" style="color:${rc.fg}">(${escapeHtml(level(r.riskLevel))})</span>` +
          `<div class="r-text">${escapeHtml(r.text)}</div></li>`,
      )
    })
    parts.push('</ol>')
  }
  if (view.steps.length) {
    parts.push(`<h2>${escapeHtml(t('verdict:pdf.steps'))}</h2><ol>${view.steps.map((s) => `<li>${escapeHtml(s)}</li>`).join('')}</ol>`)
  }

  parts.push('<div class="r-card">')
  parts.push('<div class="r-stats">')
  parts.push(
    `<span class="r-badge" style="background:${colors.bg}">${escapeHtml(t('pdf.riskBadge', { level: level(s.overall_risk) }))}</span>`,
  )
  parts.push(`<span>${escapeHtml(t('pdf.totalClauses', { count: s.total_clauses }))}</span>`)
  parts.push(`<span style="color:#e11d48">${escapeHtml(t('pdf.highRisk', { count: s.high_risk_count }))}</span>`)
  parts.push(`<span style="color:#d97706">${escapeHtml(t('pdf.mediumRisk', { count: s.medium_risk_count }))}</span>`)
  parts.push(`<span style="color:#059669">${escapeHtml(t('pdf.lowRisk', { count: s.low_risk_count }))}</span>`)
  parts.push('</div>')
  parts.push(`<div class="r-text">${escapeHtml(s.risk_summary || t('pdf.analysisComplete'))}</div>`)
  parts.push('</div>')

  const hasDetails = s.parties?.length > 0 || s.key_dates?.length > 0 || Boolean(s.document_type)
  if (hasDetails) {
    parts.push(`<h2>${escapeHtml(t('pdf.keyDetails'))}</h2>`)
    if (s.document_type) {
      parts.push(`<div><span class="r-label">${escapeHtml(t('pdf.docType'))}:</span> ${escapeHtml(s.document_type)}</div>`)
    }
    if (s.parties?.length) {
      parts.push(`<div class="r-label">${escapeHtml(t('pdf.parties'))}</div>${list(s.parties)}`)
    }
    if (s.key_dates?.length) {
      parts.push(
        `<div class="r-label">${escapeHtml(t('pdf.keyDates'))}</div>${list(s.key_dates.map((d) => `${d.label}: ${d.date}`))}`,
      )
    }
  }

  if (s.high_risk_clauses?.length) {
    parts.push(`<h2>${escapeHtml(t('pdf.highRiskList'))}</h2>${list(s.high_risk_clauses)}`)
  }
  if (s.beneficial_clauses?.length) {
    parts.push(`<h2>${escapeHtml(t('pdf.beneficialList'))}</h2>${list(s.beneficial_clauses)}`)
  }
  if (s.your_obligations?.length || s.other_party_rights?.length) {
    parts.push(`<h2>${escapeHtml(t('pdf.rightsTitle'))}</h2>`)
    if (s.your_obligations?.length) {
      parts.push(`<div class="r-label">${escapeHtml(t('pdf.yourObligations'))}</div>${list(s.your_obligations)}`)
    }
    if (s.other_party_rights?.length) {
      parts.push(`<div class="r-label">${escapeHtml(t('pdf.otherPartyRights'))}</div>${list(s.other_party_rights)}`)
    }
  }

  parts.push(`<h2>${escapeHtml(t('pdf.breakdown', { count: result.clauses.length }))}</h2>`)
  result.clauses.forEach((c, i) => {
    const rc = RISK_COLORS[c.risk_level] ?? RISK_COLORS.medium
    parts.push('<div class="r-clause">')
    parts.push(
      `<div class="r-clause-head"><span class="r-clause-title">${String(i + 1).padStart(2, '0')}. ${escapeHtml(c.title)}</span>` +
        `<span class="r-risk" style="color:${rc.fg}">${escapeHtml(
          t('pdf.clauseRisk', { level: level(c.risk_level), score: c.risk_score }),
        )}</span></div>`,
    )
    parts.push(`<div class="r-sub">${escapeHtml(t('pdf.plainSummary'))}</div>`)
    parts.push(`<div class="r-text">${escapeHtml(c.plain_english)}</div>`)
    if (c.risk_reason && c.risk_level !== 'low') {
      parts.push(`<div class="r-warn">${escapeHtml(t('pdf.riskRationale'))}</div>`)
      parts.push(`<div class="r-text">${escapeHtml(c.risk_reason)}</div>`)
    }
    parts.push('</div>')
  })

  parts.push(`<div class="r-foot">${escapeHtml(t('pdf.footer'))}</div>`)
  parts.push('</div>')
  return parts.join('')
}

// ─────────────────────────────────────────────────────────────────────────────
// jsPDF renderer: Latin script (English)
// ─────────────────────────────────────────────────────────────────────────────

/** Builds the English report. jsPDF is loaded on demand so it never weighs on the main bundle. */
export async function buildReportPdf(
  result: AnalysisResult,
  filename: string | null | undefined,
  ctx: ReportContext,
) {
  const mod = await import('jspdf')
  // Named export works in both bundlers and node; `default` is the same class in the browser build.
  const jsPDF = (mod as unknown as { jsPDF?: typeof mod.default }).jsPDF ?? mod.default
  const { t } = ctx
  const s = result.summary
  const level = (r: string) => t(`pdf.risk.${r}`, { defaultValue: r }).toUpperCase()

  const doc = new jsPDF({ orientation: 'p', unit: 'mm', format: 'a4' })
  const pageWidth = doc.internal.pageSize.getWidth()
  const pageHeight = doc.internal.pageSize.getHeight()
  const margin = 15
  const contentWidth = pageWidth - margin * 2
  let y = margin

  const addHeader = () => {
    doc.setFillColor(15, 23, 42)
    doc.rect(0, 0, pageWidth, 12, 'F')
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(9)
    doc.setTextColor(245, 194, 107)
    doc.text(t('pdf.reportHeader'), margin, 8)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8)
    doc.setTextColor(255, 255, 255)
    doc.text(ctx.dateText, pageWidth - margin, 8, { align: 'right' })
  }

  const checkPageBreak = (needed: number) => {
    if (y + needed > pageHeight - 20) {
      doc.addPage()
      y = margin
      addHeader()
    }
  }

  const addWatermark = (pageNumber: number) => {
    doc.setPage(pageNumber)
    const GState = (doc as unknown as { GState?: new (o: { opacity: number }) => unknown }).GState
    if (GState) (doc as unknown as { setGState: (g: unknown) => void }).setGState(new GState({ opacity: 0.21 }))
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(42)
    doc.setTextColor(148, 163, 184)
    doc.text('SMARTLEGAL AI', pageWidth / 2, pageHeight / 2 - 15, { align: 'center', angle: 45, rotationDirection: 0 })
    doc.setFontSize(26)
    doc.text(t('pdf.watermarkSub'), pageWidth / 2, pageHeight / 2 + 15, { align: 'center', angle: 45, rotationDirection: 0 })
    if (GState) (doc as unknown as { setGState: (g: unknown) => void }).setGState(new GState({ opacity: 1.0 }))
  }

  const addFooter = (pageNumber: number, totalPages: number) => {
    doc.setPage(pageNumber)
    doc.setDrawColor(226, 232, 240)
    doc.line(margin, pageHeight - 12, pageWidth - margin, pageHeight - 12)
    doc.setFont('helvetica', 'italic')
    doc.setFontSize(7.5)
    doc.setTextColor(100, 116, 139)
    doc.text(t('pdf.footer'), margin, pageHeight - 7)
    doc.setFont('helvetica', 'normal')
    doc.text(t('pdf.page', { page: pageNumber, total: totalPages }), pageWidth - margin, pageHeight - 7, { align: 'right' })
  }

  const bullets = (items: string[] | undefined, max = 4) => {
    ;(items ?? []).slice(0, max).forEach((item) => {
      checkPageBreak(6)
      const lines = doc.splitTextToSize(`- ${item}`, contentWidth - 6)
      doc.text(lines, margin + 4, y)
      y += lines.length * 4.5
    })
  }

  addHeader()
  y = 20

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(18)
  doc.setTextColor(15, 23, 42)
  doc.text(t('pdf.title'), margin, y)
  y += 7

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  doc.setTextColor(100, 116, 139)
  doc.text(t('pdf.file', { name: filename || s.document_type || 'Uploaded Agreement.pdf' }), margin, y)
  y += 10

  // Result at a glance: verdict, main risks, next steps (same logic and texts as the Analysis page).
  {
    const view = buildVerdictView(result, t)
    const vc = VERDICT_COLORS[view.verdict.level]
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(12)
    doc.setTextColor(15, 23, 42)
    doc.text(t('verdict:pdf.glance'), margin, y)
    y += 7
    doc.setFontSize(18)
    doc.setTextColor(vc.rgb[0], vc.rgb[1], vc.rgb[2])
    doc.text(view.levelText, margin, y)
    y += 7
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(10)
    doc.setTextColor(30, 41, 59)
    const sentenceLines = doc.splitTextToSize(view.sentence, contentWidth)
    doc.text(sentenceLines, margin, y)
    y += sentenceLines.length * 5 + 4

    const numbered = (heading: string, rows: string[]) => {
      if (!rows.length) return
      checkPageBreak(14)
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(11)
      doc.setTextColor(15, 23, 42)
      doc.text(heading, margin, y)
      y += 6
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(9.5)
      doc.setTextColor(30, 41, 59)
      rows.forEach((row, i) => {
        const lines = doc.splitTextToSize(`${i + 1}. ${row}`, contentWidth - 4)
        checkPageBreak(lines.length * 4.6 + 2)
        doc.text(lines, margin + 2, y)
        y += lines.length * 4.6 + 1.5
      })
      y += 3
    }
    numbered(
      t('verdict:pdf.risks'),
      view.risks.map((r) => `${r.title} (${level(r.riskLevel)}): ${r.text}`),
    )
    numbered(t('verdict:pdf.steps'), view.steps)
    y += 2
  }

  doc.setFillColor(248, 250, 252)
  doc.setDrawColor(226, 232, 240)
  doc.roundedRect(margin, y, contentWidth, 38, 3, 3, 'FD')

  const colors = RISK_COLORS[s.overall_risk] ?? RISK_COLORS.medium
  doc.setFillColor(colors.bg)
  doc.roundedRect(margin + 6, y + 6, 28, 7, 2, 2, 'F')
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8)
  doc.setTextColor(15, 23, 42)
  doc.text(t('pdf.riskBadge', { level: level(s.overall_risk) }), margin + 20, y + 10.5, { align: 'center' })

  doc.setFontSize(9)
  doc.text(t('pdf.totalClauses', { count: s.total_clauses }), margin + 42, y + 10.5)
  doc.setTextColor(225, 29, 72)
  doc.text(t('pdf.highRisk', { count: s.high_risk_count }), margin + 85, y + 10.5)
  doc.setTextColor(217, 119, 6)
  doc.text(t('pdf.mediumRisk', { count: s.medium_risk_count }), margin + 120, y + 10.5)
  doc.setTextColor(16, 185, 129)
  doc.text(t('pdf.lowRisk', { count: s.low_risk_count }), margin + 155, y + 10.5)

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8.5)
  doc.setTextColor(51, 65, 85)
  const summaryLines = doc.splitTextToSize(s.risk_summary || t('pdf.analysisComplete'), contentWidth - 12)
  doc.text(summaryLines.slice(0, 3), margin + 6, y + 19)
  y += 44

  if (s.parties.length > 0 || s.key_dates.length > 0) {
    checkPageBreak(30)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(12)
    doc.setTextColor(15, 23, 42)
    doc.text(t('pdf.keyDetails'), margin, y)
    y += 6
    doc.setFontSize(9)
    if (s.parties.length > 0) {
      doc.setFont('helvetica', 'bold')
      doc.text(t('pdf.parties'), margin, y)
      doc.setFont('helvetica', 'normal')
      doc.text(s.parties.join(' • '), margin + 30, y)
      y += 6
    }
    if (s.key_dates.length > 0) {
      doc.setFont('helvetica', 'bold')
      doc.text(t('pdf.keyDates'), margin, y)
      doc.setFont('helvetica', 'normal')
      const dateLines = doc.splitTextToSize(s.key_dates.map((d) => `${d.label}: ${d.date}`).join(' | '), contentWidth - 30)
      doc.text(dateLines, margin + 30, y)
      y += dateLines.length * 5 + 4
    }
    y += 2
  }

  if (s.your_obligations?.length || s.other_party_rights?.length) {
    checkPageBreak(35)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(12)
    doc.setTextColor(15, 23, 42)
    doc.text(t('pdf.rightsTitle'), margin, y)
    y += 6
    if (s.your_obligations?.length) {
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(9)
      doc.setTextColor(217, 119, 6)
      doc.text(`• ${t('pdf.yourObligations')}`, margin, y)
      y += 5
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(8.5)
      doc.setTextColor(51, 65, 85)
      bullets(s.your_obligations)
      y += 2
    }
    if (s.other_party_rights?.length) {
      checkPageBreak(15)
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(9)
      doc.setTextColor(109, 40, 217)
      doc.text(`• ${t('pdf.otherPartyRights')}`, margin, y)
      y += 5
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(8.5)
      doc.setTextColor(51, 65, 85)
      bullets(s.other_party_rights)
      y += 4
    }
  }

  checkPageBreak(25)
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(13)
  doc.setTextColor(15, 23, 42)
  doc.text(t('pdf.breakdown', { count: result.clauses.length }), margin, y)
  y += 8

  result.clauses.forEach((clause, index) => {
    checkPageBreak(38)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(10)
    doc.setTextColor(15, 23, 42)
    doc.text(`${String(index + 1).padStart(2, '0')}. ${clause.title}`, margin + 3, y + 4)

    doc.setFontSize(7.5)
    const high = clause.risk_level === 'high'
    const med = clause.risk_level === 'medium'
    doc.setTextColor(high ? 225 : med ? 180 : 16, high ? 29 : med ? 100 : 185, high ? 72 : med ? 10 : 129)
    doc.text(t('pdf.clauseRisk', { level: level(clause.risk_level), score: clause.risk_score }), pageWidth - margin, y + 4, {
      align: 'right',
    })
    y += 9

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8.5)
    doc.setTextColor(51, 65, 85)
    doc.text(t('pdf.plainSummary'), margin + 3, y)
    y += 4
    doc.setTextColor(30, 41, 59)
    const plainLines = doc.splitTextToSize(clause.plain_english, contentWidth - 6)
    doc.text(plainLines, margin + 3, y)
    y += plainLines.length * 4.2 + 2

    if (clause.risk_reason && clause.risk_level !== 'low') {
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(8)
      doc.setTextColor(225, 29, 72)
      doc.text(t('pdf.riskRationale'), margin + 3, y)
      y += 4
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(71, 85, 105)
      const reasonLines = doc.splitTextToSize(clause.risk_reason, contentWidth - 6)
      doc.text(reasonLines, margin + 3, y)
      y += reasonLines.length * 4 + 2
    }

    doc.setDrawColor(226, 232, 240)
    doc.line(margin, y, pageWidth - margin, y)
    y += 6
  })

  const totalPages = doc.getNumberOfPages()
  for (let i = 1; i <= totalPages; i++) {
    addWatermark(i)
    addFooter(i, totalPages)
  }
  return doc
}
