export default function WhatsAppDocumentUseCase() {
  return (
    <div className="rounded-3xl border border-emerald-500/20 bg-gradient-to-r from-emerald-950/20 via-slate-900/60 to-slate-950 p-8 sm:p-10 shadow-xl backdrop-blur-md">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-8">
        <div className="space-y-4 max-w-xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400">
            <span>Supported Formats: PDF & Image (Up to 10 MB)</span>
          </div>

          <h2 className="text-2xl font-bold text-white sm:text-3xl tracking-tight">
            Have a document? Send it on WhatsApp.
          </h2>

          <p className="text-sm text-slate-300 leading-relaxed">
            Send an agreement, contract, or supported legal document directly in your chat. SmartLegal-AI analyzes it and helps you understand important clauses, risk ratings, and next steps.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4 w-full md:w-auto">
          <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 text-center space-y-1">
            <div className="text-2xl">📄</div>
            <div className="text-xs font-bold text-slate-200">PDF Documents</div>
            <div className="text-[10px] text-slate-400">Rental, employment, NDA</div>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 text-center space-y-1">
            <div className="text-2xl">🖼️</div>
            <div className="text-xs font-bold text-slate-200">Image Files</div>
            <div className="text-[10px] text-slate-400">PNG, JPG, WebP contract photos</div>
          </div>
        </div>
      </div>
    </div>
  )
}
