import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { formatNumber, formatPercent } from '../../utils/i18nHelpers'
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

function reasonKey(errorType?: string): string {
  if (!errorType) return 'default'
  const lower = errorType.toLowerCase()
  if (lower.includes('rate') || lower.includes('429')) return 'capacity'
  if (lower.includes('timeout') || lower.includes('transient')) return 'timeout'
  if (lower.includes('unclear') || lower.includes('scanned') || lower.includes('quality')) return 'scan'
  return 'processing'
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
  const { t, i18n } = useTranslation('analysis')
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false)
  const pct =
    completionRatio != null
      ? formatPercent(completionRatio, i18n.language)
      : totalChunks && successfulChunks
      ? formatPercent(successfulChunks / totalChunks, i18n.language)
      : null

  // Format distinct page spans from incompleteChunks
  const unanalyzedSpans = (incompleteChunks || [])
    .filter((c) => c.page_start != null && c.page_end != null)
    .map((c) => {
      const pageText =
        c.page_start === c.page_end
          ? t('partial.page', { page: formatNumber(c.page_start as number, i18n.language) })
          : t('partial.pages', {
              start: formatNumber(c.page_start as number, i18n.language),
              end: formatNumber(c.page_end as number, i18n.language),
            })
      return {
        text: pageText,
        reason: t(`partial.reason.${reasonKey(c.error_type)}`),
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
                {t('partial.title')}
              </h2>
              {pct != null ? (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-400/20 text-amber-300 border border-amber-400/40">
                  {t('partial.pctBadge', { pct })}
                </span>
              ) : (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-400/20 text-amber-300 border border-amber-400/40">
                  {t('partial.badge')}
                </span>
              )}
            </div>
            <p className="text-sm text-slate-300 leading-relaxed max-w-2xl">
              {t('partial.body')}
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
                title={t('partial.reanalyzeTitle')}
                aria-label={t('partial.reanalyzeAria')}
                className="min-h-[44px] px-4 py-2.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-400/40 font-semibold text-xs transition flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-amber-400 disabled:opacity-50"
              >
                <span aria-hidden="true">{isReanalyzing ? '⏳' : '🔄'}</span>
                <span>{isReanalyzing ? t('partial.reanalyzing') : t('partial.reanalyze')}</span>
              </button>
              <span className="text-[10px] text-slate-400 max-w-[210px] leading-tight text-left sm:text-right">
                {t('partial.reanalyzeHint')}
              </span>
            </div>
          )}

          {onAskAdvocate && (
            <button
              type="button"
              onClick={onAskAdvocate}
              aria-label={t('partial.askAdvocateAria')}
              className="min-h-[44px] px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs transition shadow-lg shadow-amber-500/20 flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-white"
            >
              <span aria-hidden="true">⚖️</span>
              <span>{t('partial.askAdvocate')}</span>
            </button>
          )}
        </div>
      </div>

      {/* Unanalyzed Page Badges */}
      {unanalyzedSpans.length > 0 && (
        <div className="pt-3 border-t border-white/5 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold text-slate-300">
              {t('partial.unprocessed')}
            </span>
            <button
              type="button"
              onClick={() => setShowTechnicalDetails((p) => !p)}
              className="text-[11px] text-amber-400/80 hover:text-amber-300 underline underline-offset-2"
            >
              {showTechnicalDetails ? t('partial.hideDetails') : t('partial.showDetails')}
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
                  {t('partial.spanReason', { span: span.text, reason: span.reason })}
                </span>
              </span>
            ))}
          </div>
          {showTechnicalDetails && totalChunks && (
            <p className="text-[11px] text-slate-400 pt-1">
              {t('partial.chunks', { ok: formatNumber(successfulChunks ?? 0, i18n.language), total: formatNumber(totalChunks, i18n.language) })}
            </p>
          )}
        </div>
      )}

      {/* Advocates Act, 1961 Legal Disclaimer note */}
      <div className="pt-2 text-[11px] text-slate-400/90 flex items-center gap-1.5">
        <span aria-hidden="true">ℹ️</span>
        <span>
          {t('partial.preliminary')}
        </span>
      </div>
    </div>
  )
}
