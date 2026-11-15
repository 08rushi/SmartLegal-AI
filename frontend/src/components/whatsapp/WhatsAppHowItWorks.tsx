import { useTranslation } from 'react-i18next'

const steps = [
  { number: '01', key: 'open' },
  { number: '02', key: 'send' },
  { number: '03', key: 'help' },
]

export default function WhatsAppHowItWorks() {
  const { t } = useTranslation('whatsapp')
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-bold text-white tracking-tight">
          {t('howItWorks.title')}
        </h2>
        <p className="text-sm text-slate-400">
          {t('howItWorks.subtitle')}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {steps.map((step) => (
          <div
            key={step.number}
            className="relative rounded-2xl border border-slate-800/80 bg-slate-900/40 p-6 space-y-3"
          >
            <div className="text-3xl font-black text-amber-400/30">{step.number}</div>
            <h3 className="text-base font-bold text-white">{t(`howItWorks.steps.${step.key}.title`)}</h3>
            <p className="text-xs text-slate-400 leading-relaxed">{t(`howItWorks.steps.${step.key}.description`)}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
