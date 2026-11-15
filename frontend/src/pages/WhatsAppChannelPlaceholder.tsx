import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export default function WhatsAppChannelPlaceholder() {
  const { t } = useTranslation('whatsapp')
  return (
    <div className="page-shell bg-app min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="content-wrap max-w-4xl mx-auto space-y-8">
        {/* Header Breadcrumb / Navigation */}
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <Link to="/" className="hover:text-amber-400 transition">
            {t('breadcrumb.home')}
          </Link>
          <span>/</span>
          <span className="text-slate-200">{t('breadcrumb.channels')}</span>
          <span>/</span>
          <span className="text-emerald-400 font-medium">{t('breadcrumb.current')}</span>
        </div>

        {/* Hero Card */}
        <div className="rounded-3xl border border-emerald-500/20 bg-gradient-to-b from-emerald-950/30 via-slate-900/90 to-slate-950 p-8 shadow-2xl backdrop-blur-md space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-4 py-1.5 text-xs font-semibold text-emerald-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            {t('placeholder.eyebrow')}
          </div>

          <h1 className="text-3xl font-extrabold text-white sm:text-4xl">
            {t('placeholder.title')}
          </h1>

          <p className="text-slate-300 text-base leading-relaxed max-w-2xl">
            {t('placeholder.body')}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
              <div className="text-lg font-bold text-amber-400">{t('placeholder.instantTitle')}</div>
              <p className="text-xs text-slate-400">{t('placeholder.instantBody')}</p>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
              <div className="text-lg font-bold text-emerald-400">{t('placeholder.multiTitle')}</div>
              <p className="text-xs text-slate-400">{t('placeholder.multiBody')}</p>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
              <div className="text-lg font-bold text-sky-400">{t('placeholder.confTitle')}</div>
              <p className="text-xs text-slate-400">{t('placeholder.confBody')}</p>
            </div>
          </div>

          <div className="pt-6 border-t border-slate-800 flex flex-wrap gap-4 items-center justify-between">
            <p className="text-xs text-slate-400">
              {t('placeholder.hub')}
            </p>
            <Link
              to="/"
              className="rounded-xl border border-slate-700 bg-slate-800 px-5 py-2.5 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition"
            >
              {t('placeholder.backHome')}
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
