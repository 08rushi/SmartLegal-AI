import { Trans, useTranslation } from 'react-i18next'

// Native names are always shown in their own script (same in every UI language).
const languages = [
  { code: 'EN', key: 'en', native: 'English' },
  { code: 'HI', key: 'hi', native: 'हिंदी' },
  { code: 'MR', key: 'mr', native: 'मराठी' },
]

export default function WhatsAppLanguageSupport() {
  const { t } = useTranslation('whatsapp')
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-bold text-white tracking-tight">
          {t('languageSupport.title')}
        </h2>
        <p className="text-sm text-slate-400">
          <Trans
            t={t}
            i18nKey="languageSupport.subtitle"
            values={{ command: 'language' }} // the bot's literal keyword; never translated
          />
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {languages.map((lang) => (
          <div
            key={lang.code}
            className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 space-y-2"
          >
            <div className="flex items-center justify-between">
              <span className="rounded-md border border-amber-400/30 bg-amber-400/10 px-2 py-0.5 text-xs font-bold text-amber-400">
                {lang.code}
              </span>
              <span className="text-base font-bold text-white">{lang.native}</span>
            </div>
            <h3 className="text-sm font-semibold text-slate-200">{t(`languageSupport.languages.${lang.key}.name`)}</h3>
            <p className="text-xs text-slate-400 leading-relaxed">{t(`languageSupport.languages.${lang.key}.desc`)}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
