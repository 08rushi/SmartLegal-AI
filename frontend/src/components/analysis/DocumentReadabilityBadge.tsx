import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { formatPercent } from '../../utils/i18nHelpers'

interface DocumentReadabilityBadgeProps {
  pageType?: 'digital' | 'scanned' | 'empty' | string
  qualityScore?: number | null
  ocrConfidence?: number | null
}

export function DocumentReadabilityBadge({
  pageType = 'digital',
  qualityScore,
  ocrConfidence,
}: DocumentReadabilityBadgeProps) {
  const { t, i18n } = useTranslation('analysis')
  const [showTooltip, setShowTooltip] = useState(false)
  const isDigital = pageType === 'digital'
  const isScanned = pageType === 'scanned'

  // Format OCR confidence string preserving null/unknown semantics
  let confidenceLabel: string
  if (isDigital) {
    confidenceLabel = t('readability.notApplicable')
  } else if (ocrConfidence === null || ocrConfidence === undefined) {
    confidenceLabel = t('readability.notAvailable')
  } else {
    confidenceLabel = t('readability.legibilityPct', { pct: formatPercent(ocrConfidence, i18n.language) })
  }

  // Format technical quality string strictly as typographic readability
  let readabilityGrade = t('readability.grade.high')
  if (qualityScore != null) {
    if (qualityScore < 0.5) readabilityGrade = t('readability.grade.degraded')
    else if (qualityScore < 0.75) readabilityGrade = t('readability.grade.fair')
  }

  const badgeLabel = isDigital
    ? t('readability.badge.digital')
    : isScanned
    ? t('readability.badge.scanned')
    : t('readability.badge.other')

  return (
    <div className="relative inline-block align-middle">
      <button
        type="button"
        onClick={() => setShowTooltip((p) => !p)}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onFocus={() => setShowTooltip(true)}
        onBlur={() => setShowTooltip(false)}
        aria-label={t('readability.aria', { label: badgeLabel })}
        aria-expanded={showTooltip}
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border transition focus:outline-none focus:ring-2 focus:ring-amber-400 ${
          isDigital
            ? 'bg-blue-500/10 border-blue-500/25 text-blue-300 hover:bg-blue-500/20'
            : isScanned
            ? 'bg-amber-500/10 border-amber-500/25 text-amber-300 hover:bg-amber-500/20'
            : 'bg-slate-800 border-slate-700 text-slate-300'
        }`}
      >
        <span aria-hidden="true">{isDigital ? '📄' : '🔍'}</span>
        <span>{badgeLabel}</span>
      </button>

      {showTooltip && (
        <div
          role="tooltip"
          className="absolute z-50 top-full left-0 mt-2 w-80 max-w-[85vw] p-3.5 rounded-2xl bg-slate-900/95 border border-slate-700/80 text-xs text-slate-200 shadow-2xl backdrop-blur-md animate-fadeIn space-y-2 text-left"
        >
          <div className="font-bold text-white flex items-center justify-between">
            <span>{t('readability.tooltipTitle')}</span>
            <span className="text-[10px] text-amber-400 uppercase tracking-wider font-semibold">
              {t('readability.notLegalAdvice')}
            </span>
          </div>

          <div className="space-y-1 text-slate-300 leading-relaxed text-[11px]">
            <p>
              <strong>{t('readability.source')}</strong>{' '}
              {isDigital
                ? t('readability.sourceDigital')
                : t('readability.sourceScanned')}
            </p>
            <p>
              <strong>{t('readability.ocrLegibility')}</strong> {confidenceLabel}
            </p>
            {qualityScore != null && (
              <p>
                <strong>{t('readability.typographic')}</strong>{' '}
                {t('readability.coherence', { grade: readabilityGrade, pct: formatPercent(qualityScore, i18n.language) })}
              </p>
            )}
          </div>

          <p className="text-[10px] text-slate-400/90 pt-1 border-t border-slate-800 italic">
            {t('readability.notice')}
          </p>
        </div>
      )}
    </div>
  )
}
