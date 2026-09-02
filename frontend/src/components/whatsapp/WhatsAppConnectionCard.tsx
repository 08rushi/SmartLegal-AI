export type ConnectionState = 'not_connected' | 'preparing' | 'connected'

interface WhatsAppConnectionCardProps {
  state?: ConnectionState
  onStartClick?: () => void
}

export default function WhatsAppConnectionCard({
  state = 'preparing',
  onStartClick,
}: WhatsAppConnectionCardProps) {
  return (
    <div id="connection-card" className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400 animate-pulse" />
            <span className="text-xs font-semibold uppercase tracking-wider text-amber-400">
              Channel Status
            </span>
          </div>

          <h3 className="text-lg font-bold text-white">
            {state === 'connected' ? 'WhatsApp Connected' : 'WhatsApp connection is being prepared.'}
          </h3>

          <p className="text-xs text-slate-400 max-w-xl">
            {state === 'connected'
              ? 'SmartLegal-AI is ready on your WhatsApp account.'
              : 'Our secure Meta WhatsApp Cloud API integration is being prepared for live onboarding. You can explore all supported capabilities below.'}
          </p>
        </div>

        <div>
          <button
            onClick={onStartClick}
            className="w-full sm:w-auto rounded-xl border border-emerald-400/40 bg-emerald-500/10 px-5 py-2.5 text-xs font-semibold text-emerald-400 transition hover:bg-emerald-500/20"
          >
            {state === 'connected' ? 'Open WhatsApp' : 'Start on WhatsApp'}
          </button>
        </div>
      </div>
    </div>
  )
}
