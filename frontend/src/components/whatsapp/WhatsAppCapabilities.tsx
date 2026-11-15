import { useTranslation } from 'react-i18next'

const capabilities = [
  { icon: '⚖️', key: 'questions' },
  { icon: '📄', key: 'analysis' },
  { icon: '🚨', key: 'risk' },
  { icon: '✍️', key: 'drafting' },
  { icon: '💬', key: 'context' },
  { icon: '🌐', key: 'multilingual' },
]

export default function WhatsAppCapabilities() {
  const { t } = useTranslation('whatsapp')
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h2 className="text-2xl font-bold text-white tracking-tight">
          {t('capabilities.title')}
        </h2>
        <p className="text-sm text-slate-400">
          {t('capabilities.subtitle')}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {capabilities.map((item) => (
          <div
            key={item.key}
            className="rounded-2xl border border-slate-800/80 bg-slate-900/50 p-6 space-y-3 transition duration-200 hover:border-slate-700 hover:bg-slate-900/80"
          >
            <div className="text-2xl">{item.icon}</div>
            <h3 className="text-base font-bold text-slate-100">{t(`capabilities.items.${item.key}.title`)}</h3>
            <p className="text-xs text-slate-400 leading-relaxed">{t(`capabilities.items.${item.key}.description`)}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
