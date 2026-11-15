import { useTranslation } from 'react-i18next'

export default function WhatsAppSecuritySection() {
  const { t } = useTranslation('whatsapp')
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 sm:p-8 space-y-4">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-emerald-400/30 bg-emerald-500/10 text-emerald-400">
          🛡️
        </div>
        <div>
          <h3 className="text-lg font-bold text-white">{t('security.title')}</h3>
          <p className="text-xs text-slate-400">{t('security.subtitle')}</p>
        </div>
      </div>

      <p className="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-3xl">
        {t('security.body')}
      </p>
    </div>
  )
}
