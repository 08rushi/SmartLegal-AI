import { useState } from 'react'
import type { IncompleteChunkInfo } from '../../types'

interface PartialAnalysisAlertProps {
  completionRatio?: number
  totalChunks?: number
  successfulChunks?: number
  incompleteChunks?: IncompleteChunkInfo[]
  onReanalyze?: () => void
  onAskAdvocate?: () => void
  isReanalyzing?: boolean
}

function formatErrorReason(errorType?: string): string {
  if (!errorType) return 'temporary service limitation'
  const lower = errorType.toLowerCase()
  if (lower.includes('rate') || lower.includes('429')) return 'server capacity limit'
  if (lower.includes('timeout') || lower.includes('transient')) return 'network timeout'
  if (lower.includes('unclear') || lower.includes('scanned') || lower.includes('quality')) return 'scan legibility limits'
  return 'temporary processing limitation'
}

export function PartialAnalysisAlert({
  completionRatio,
  totalChunks,
  successfulChunks,
  incompleteChunks,
  onReanalyze,
  onAskAdvocate,
  isReanalyzing = false,
}: PartialAnalysisAlertProps) {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false)
  const pct =
    completionRatio != null
      ? Math.round(completionRatio * 100)
      : totalChunks && successfulChunks
      ? Math.round((successfulChunks / totalChunks) * 100)
      : null

  // Format distinct page spans from incompleteChunks
  const unanalyzedSpans = (incompleteChunks || [])
    .filter((c) => c.page_start != null && c.page_end != null)
    .map((c) => {
      const pageText =
        c.page_start === c.page_end
          ? `Page ${c.page_start}`
          : `Pages ${c.page_start}–${c.page_end}`
      return {
        text: pageText,
        reason: formatErrorReason(c.error_type),
      }
    })

  return (
    <div
      role="alert"
      aria-live="polite"
      className="rounded-3xl border border-amber-500/35 bg-gradient-to-r from-amber-950/40 via-slate-900/90 to-slate-950 p-5 sm:p-7 shadow-2xl backdrop-blur-xl space-y-4 mb-6"
    >
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <div className="flex items-start gap-4">
          <div
            className="h-12 w-12 rounded-2xl bg-amber-500/20 border border-amber-400/40 flex items-center justify-center text-2xl text-amber-400 shrink-0 shadow-lg shadow-amber-500/10"
            aria-hidden="true"
          >
            ⚠️
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5 flex-wrap">
              <h2 className="text-lg font-bold text-white tracking-tight">
                Partial Document Analysis
              </h2>
              {pct != null ? (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-400/20 text-amber-300 border border-amber-400/40">
                  {pct}% Analyzed
                </span>
              ) : (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-400/20 text-amber-300 border border-amber-400/40">
                  Partial Analysis
                </span>
              )}
            </div>
            <p className="text-sm text-slate-300 leading-relaxed max-w-2xl">
              Some sections of this document could not be analyzed due to temporary service limitations or low scan clarity. The verified clauses from the analyzed sections are shown below.
            </p>
          </div>
        </div>

        {/* Action Buttons: Min touch target 44px */}
        <div className="flex flex-wrap sm:flex-nowrap items-center gap-3 shrink-0 pt-2 md:pt-0">
          {onReanalyze && (
            <div className="flex flex-col items-start sm:items-end gap-1">
              <button
                type="button"
                onClick={onReanalyze}
                disabled={isReanalyzing}
                title="This will re-run analysis across the entire document, including previously analyzed pages."
                aria-label="Re-analyze entire document. This will re-run analysis across the entire document, including previously analyzed pages."
                className="min-h-[44px] px-4 py-2.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-400/40 font-semibold text-xs transition flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-amber-400 disabled:opacity-50"
              >
                <span aria-hidden="true">{isReanalyzing ? '⏳' : '🔄'}</span>
                <span>{isReanalyzing ? 'Re-analyzing...' : 'Re-analyze Document'}</span>
              </button>
              <span className="text-[10px] text-slate-400 max-w-[210px] leading-tight text-left sm:text-right">
                Re-runs analysis across entire document
              </span>
            </div>
          )}

          {onAskAdvocate && (
            <button
              type="button"
              onClick={onAskAdvocate}
              aria-label="Ask a verified advocate for formal legal review"
              className="min-h-[44px] px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs transition shadow-lg shadow-amber-500/20 flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-white"
            >
              <span aria-hidden="true">⚖️</span>
              <span>Ask Advocate</span>
            </button>
          )}
        </div>
      </div>

      {/* Unanalyzed Page Badges */}
      {unanalyzedSpans.length > 0 && (
        <div className="pt-3 border-t border-white/5 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold text-slate-300">
              Unprocessed Document Sections:
            </span>
            <button
              type="button"
              onClick={() => setShowTechnicalDetails((p) => !p)}
              className="text-[11px] text-amber-400/80 hover:text-amber-300 underline underline-offset-2"
            >
              {showTechnicalDetails ? 'Hide details' : 'Show details'}
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {unanalyzedSpans.map((span, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-rose-500/10 border border-rose-500/25 text-rose-200 text-xs font-medium"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
                <span>
                  {span.text} ({span.reason})
                </span>
              </span>
            ))}
          </div>
          {showTechnicalDetails && totalChunks && (
            <p className="text-[11px] text-slate-400 pt-1">
              {successfulChunks ?? 0} of {totalChunks} document sections were analyzed successfully.
            </p>
          )}
        </div>
      )}

      {/* Advocates Act, 1961 Legal Disclaimer note */}
      <div className="pt-2 text-[11px] text-slate-400/90 flex items-center gap-1.5">
        <span aria-hidden="true">ℹ️</span>
        <span>
          Risk assessments shown below are preliminary and calculated based solely on the analyzed sections.
        </span>
      </div>
    </div>
  )
}
