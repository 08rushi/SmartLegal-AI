import i18n from '../i18n'
import { DEFAULT_LANGUAGE, LANGUAGES, normalizeLanguage } from '../i18n/languages'
import type { AnalysisResult, UploadedDocument } from '../types'
import { formatLocalDate } from './i18nHelpers'
import {
  PRINT_ROOT_ID,
  buildReportHtml,
  buildReportPdf,
  reportCss,
  reportFileBase,
  type ReportContext,
} from './pdfReport'

/**
 * Exports the analysis report in the selected language.
 *
 *  - English: jsPDF, direct .pdf download (Latin text, built-in fonts).
 *  - Hindi / Marathi: jsPDF cannot shape Devanagari (conjuncts/matras break with any embedded TTF),
 *    so the report is rendered by the browser (HarfBuzz shaping, bundled Noto Sans Devanagari) in a
 *    print-only DOM block and the print dialog opens ("Save as PDF"). Nothing is fetched at runtime.
 *
 * `result` must already be the view for `lang` (translated analysis for hi/mr).
 */
export async function exportAnalysisToPDF(
  result: AnalysisResult,
  document?: UploadedDocument | null,
  lang?: string,
  options: { translated?: boolean } = {},
): Promise<void> {
  const code = normalizeLanguage(lang ?? i18n.language) ?? DEFAULT_LANGUAGE
  const ctx: ReportContext = {
    t: i18n.getFixedT(code, 'analysis') as ReportContext['t'],
    lang: code,
    dateText: formatLocalDate(new Date(), { day: 'numeric', month: 'short', year: 'numeric' }, code),
    languageName: LANGUAGES.find((l) => l.code === code)?.nativeName ?? code,
    translated: options.translated ?? code !== 'en',
  }
  const base = reportFileBase(result, document?.filename)

  if (code === 'en') {
    const pdf = await buildReportPdf(result, document?.filename, ctx)
    pdf.save(`${base}.pdf`)
    return
  }
  await printReport(buildReportHtml(result, document?.filename, ctx), base, code)
}

/** Renders `html` into a print-only block and opens the print dialog; cleans up afterwards. */
async function printReport(html: string, title: string, lang: string): Promise<void> {
  const doc = window.document
  doc.getElementById(PRINT_ROOT_ID)?.remove()
  doc.getElementById(`${PRINT_ROOT_ID}-style`)?.remove()

  const style = doc.createElement('style')
  style.id = `${PRINT_ROOT_ID}-style`
  style.textContent = reportCss()
  const root = doc.createElement('div')
  root.id = PRINT_ROOT_ID
  root.setAttribute('lang', lang)
  root.innerHTML = html
  doc.head.appendChild(style)
  doc.body.appendChild(root)

  // Make sure the Devanagari font faces (lazy, unicode-range subset) are loaded before printing.
  try {
    const sample = root.textContent?.slice(0, 400) || 'अ'
    await Promise.all([
      doc.fonts.load('400 11pt "Noto Sans Devanagari"', sample),
      doc.fonts.load('700 11pt "Noto Sans Devanagari"', sample),
    ])
    await doc.fonts.ready
  } catch {
    /* font loading API unavailable: print with whatever is loaded */
  }

  // The default "Save as PDF" file name comes from the page title.
  const previousTitle = doc.title
  doc.title = title

  const cleanup = () => {
    doc.title = previousTitle
    root.remove()
    style.remove()
    window.removeEventListener('afterprint', cleanup)
  }
  window.addEventListener('afterprint', cleanup)
  // Root is display:none on screen; the print stylesheet reveals it. Let layout settle first.
  await new Promise((resolve) => requestAnimationFrame(() => resolve(null)))
  window.print()
}
