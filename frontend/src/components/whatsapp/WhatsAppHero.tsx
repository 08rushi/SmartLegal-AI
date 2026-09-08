import { Link } from 'react-router-dom'

interface WhatsAppHeroProps {
  onStartClick?: () => void
}

export default function WhatsAppHero({ onStartClick }: WhatsAppHeroProps) {
  return (
    <div className="relative overflow-hidden rounded-3xl border border-emerald-500/20 bg-gradient-to-b from-slate-900/90 via-slate-900/70 to-slate-950 p-8 sm:p-12 shadow-2xl backdrop-blur-md">
      {/* Background ambient glow */}
      <div className="pointer-events-none absolute -top-24 -right-24 h-72 w-72 rounded-full bg-emerald-500/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -left-24 h-72 w-72 rounded-full bg-amber-500/10 blur-3xl" />

      <div className="relative space-y-6 max-w-3xl">
        {/* Eyebrow */}
        <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3.5 py-1 text-xs font-bold uppercase tracking-wider text-emerald-400">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          SmartLegal AI on WhatsApp
        </div>

        {/* Main Heading */}
        <h1 className="text-3xl font-extrabold text-white sm:text-5xl leading-tight tracking-tight">
          Your Legal Assistant, <br className="hidden sm:inline" />
          <span className="text-gradient">Right Inside WhatsApp.</span>
        </h1>

        {/* Supporting Copy */}
        <p className="text-base sm:text-lg text-slate-300 leading-relaxed">
          Ask legal questions, send documents, understand risks, and get clear legal guidance directly on WhatsApp.
        </p>

        {/* Action Buttons */}
        <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
          <button
            onClick={onStartClick}
            className="flex items-center justify-center gap-2 rounded-xl bg-[linear-gradient(180deg,#25D366,#128C7E)] px-6 py-3.5 text-sm font-semibold text-slate-950 shadow-[0_10px_30px_rgba(37,211,102,0.3)] transition hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-emerald-400"
          >
            <span>Start on WhatsApp</span>
            <span className="text-base">→</span>
          </button>

          <Link
            to="/"
            className="flex items-center justify-center rounded-xl border border-slate-700/80 bg-slate-800/60 px-6 py-3.5 text-sm font-medium text-slate-200 transition hover:bg-slate-800 hover:text-white"
          >
            Back to SmartLegal AI
          </Link>
        </div>
      </div>
    </div>
  )
}
