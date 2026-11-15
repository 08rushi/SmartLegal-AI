import { useTranslation } from 'react-i18next'

interface BeforeYouSignChecklistProps {
  healthScore: number
  obligations: string[]
  highRiskCount: number
  lockInMonths?: number
  noticeDays?: number
}

export function BeforeYouSignChecklist({
  healthScore,
  obligations,
  highRiskCount,
  lockInMonths = 11,
  noticeDays = 30,
}: BeforeYouSignChecklistProps) {
  const { t } = useTranslation('analysis')
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-400 border-emerald-400/30 bg-emerald-400/10'
    if (score >= 60) return 'text-amber-400 border-amber-400/30 bg-amber-400/10'
    return 'text-rose-400 border-rose-400/30 bg-rose-400/10'
  }

  return (
    <div className="bg-[#121a2d]/90 border border-slate-800 rounded-3xl p-6 backdrop-blur-xl space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <span>✍️</span>
            <span>{t('checklist.title')}</span>
          </h3>
          <p className="text-slate-400 text-xs mt-1">
            {t('checklist.subtitle')}
          </p>
        </div>

        {/* Contract Health Score (SL-065) */}
        <div className={`border px-4 py-2 rounded-2xl text-center ${getScoreColor(healthScore)}`}>
          <div className="text-xs uppercase font-bold tracking-wider">{t('checklist.healthScore')}</div>
          <div className="text-2xl font-black">{healthScore} / 100</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl space-y-1">
          <div className="text-xs text-slate-400 font-bold uppercase">{t('checklist.lockIn')}</div>
          <div className="text-lg font-bold text-amber-400">{t('checklist.months', { count: lockInMonths })}</div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl space-y-1">
          <div className="text-xs text-slate-400 font-bold uppercase">{t('checklist.notice')}</div>
          <div className="text-lg font-bold text-amber-400">{t('checklist.days', { count: noticeDays })}</div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl space-y-1">
          <div className="text-xs text-slate-400 font-bold uppercase">{t('checklist.highWarnings')}</div>
          <div className="text-lg font-bold text-rose-400">{t('checklist.clauses', { count: highRiskCount })}</div>
        </div>
      </div>

      {obligations.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            {t('checklist.obligations')}
          </h4>
          <ul className="space-y-2">
            {obligations.map((ob, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-300">
                <span className="text-amber-400 font-bold">✓</span>
                <span>{ob}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
