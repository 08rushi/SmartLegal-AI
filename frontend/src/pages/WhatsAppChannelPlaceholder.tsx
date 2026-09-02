import { Link } from 'react-router-dom'

export default function WhatsAppChannelPlaceholder() {
  return (
    <div className="page-shell bg-app min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="content-wrap max-w-4xl mx-auto space-y-8">
        {/* Header Breadcrumb / Navigation */}
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <Link to="/" className="hover:text-amber-400 transition">
            Home
          </Link>
          <span>/</span>
          <span className="text-slate-200">Channels</span>
          <span>/</span>
          <span className="text-emerald-400 font-medium">WhatsApp AI Channel</span>
        </div>

        {/* Hero Card */}
        <div className="rounded-3xl border border-emerald-500/20 bg-gradient-to-b from-emerald-950/30 via-slate-900/90 to-slate-950 p-8 shadow-2xl backdrop-blur-md space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-4 py-1.5 text-xs font-semibold text-emerald-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            Official SmartLegal AI Channel
          </div>

          <h1 className="text-3xl font-extrabold text-white sm:text-4xl">
            WhatsApp AI Legal Assistant
          </h1>

          <p className="text-slate-300 text-base leading-relaxed max-w-2xl">
            Analyze legal agreements, verify government scheme eligibility, and receive plain-language explanations in English & Hindi directly on WhatsApp.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
              <div className="text-lg font-bold text-amber-400">⚡ Instant Review</div>
              <p className="text-xs text-slate-400">Upload agreements and contracts via WhatsApp chat for instant risk breakdown.</p>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
              <div className="text-lg font-bold text-emerald-400">🌐 Multilingual</div>
              <p className="text-xs text-slate-400">Seamlessly switch responses between English and Hindi.</p>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
              <div className="text-lg font-bold text-sky-400">🛡️ 100% Confidential</div>
              <p className="text-xs text-slate-400">Encrypted messaging integrated directly into SmartLegal security infrastructure.</p>
            </div>
          </div>

          <div className="pt-6 border-t border-slate-800 flex flex-wrap gap-4 items-center justify-between">
            <p className="text-xs text-slate-400">
              SmartLegal AI WhatsApp Integration Hub Placeholder
            </p>
            <Link
              to="/"
              className="rounded-xl border border-slate-700 bg-slate-800 px-5 py-2.5 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition"
            >
              Back to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
