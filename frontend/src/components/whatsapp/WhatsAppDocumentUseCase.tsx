import { useTranslation } from 'react-i18next'

export default function WhatsAppDocumentUseCase() {
  const { t } = useTranslation('whatsapp')
  return (
    <div className="rounded-3xl border border-emerald-500/20 bg-gradient-to-r from-emerald-950/20 via-slate-900/60 to-slate-950 p-8 sm:p-10 shadow-xl backdrop-blur-md">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-8">
        <div className="space-y-4 max-w-xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400">
            <span>{t('documentUseCase.formats')}</span>
          </div>

          <h2 className="text-2xl font-bold text-white sm:text-3xl tracking-tight">
            {t('documentUseCase.title')}
          </h2>

          <p className="text-sm text-slate-300 leading-relaxed">
            {t('documentUseCase.body')}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4 w-full md:w-auto">
          <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 text-center space-y-1">
            <div className="text-2xl">📄</div>
            <div className="text-xs font-bold text-slate-200">{t('documentUseCase.pdfTitle')}</div>
            <div className="text-[10px] text-slate-400">{t('documentUseCase.pdfExamples')}</div>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 text-center space-y-1">
            <div className="text-2xl">🖼️</div>
            <div className="text-xs font-bold text-slate-200">{t('documentUseCase.imageTitle')}</div>
            <div className="text-[10px] text-slate-400">{t('documentUseCase.imageExamples')}</div>
          </div>
        </div>
      </div>
    </div>
  )
}
