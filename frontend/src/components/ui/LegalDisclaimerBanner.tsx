import { Trans, useTranslation } from 'react-i18next'

export function LegalDisclaimerBanner() {
  const { t } = useTranslation('escalation')
  return (
    <div className="bg-[#121a2d]/80 border border-slate-800 rounded-2xl p-4 text-xs text-slate-400 space-y-1 backdrop-blur-xl">
      <div className="flex items-center gap-2 font-bold text-amber-400">
        <span>⚖️</span>
        <span className="uppercase tracking-wider">{t('disclaimer.title')}</span>
      </div>
      <p className="leading-relaxed">
        <Trans t={t} i18nKey="disclaimer.body" components={{ b: <strong /> }} />
      </p>
    </div>
  )
}
