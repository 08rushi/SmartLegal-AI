import { useTranslation } from 'react-i18next'

export type ConnectionState = 'not_connected' | 'preparing' | 'connected'

interface WhatsAppConnectionCardProps {
  state?: ConnectionState
  onStartClick?: () => void
}

export default function WhatsAppConnectionCard({
  state = 'preparing',
  onStartClick,
}: WhatsAppConnectionCardProps) {
  const { t } = useTranslation('whatsapp')
  return (
    <div id="connection-card" className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400 animate-pulse" />
            <span className="text-xs font-semibold uppercase tracking-wider text-amber-400">
              {t('connection.channelStatus')}
            </span>
          </div>

          <h3 className="text-lg font-bold text-white">
            {state === 'connected' ? t('connection.connectedTitle') : t('connection.preparingTitle')}
          </h3>

          <p className="text-xs text-slate-400 max-w-xl">
            {state === 'connected' ? t('connection.connectedBody') : t('connection.preparingBody')}
          </p>
        </div>

        <div>
          <button
            onClick={onStartClick}
            className="w-full sm:w-auto rounded-xl border border-emerald-400/40 bg-emerald-500/10 px-5 py-2.5 text-xs font-semibold text-emerald-400 transition hover:bg-emerald-500/20"
          >
            {state === 'connected' ? t('connection.open') : t('connection.start')}
          </button>
        </div>
      </div>
    </div>
  )
}
