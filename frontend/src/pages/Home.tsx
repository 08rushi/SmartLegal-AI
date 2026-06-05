import { Link } from 'react-router-dom'

const practiceAreas = [
  {
    title: 'Rental Agreement',
    description: 'Analyze lease terms, rent clauses, deposit rules, and notice periods.',
    accent: 'from-[#2a3152] to-[#121a2d]',
  },
  {
    title: 'Employment Contract',
    description: 'Review salary terms, probation, termination, and restrictive clauses.',
    accent: 'from-[#241d41] to-[#121a2d]',
  },
  {
    title: 'Loan Agreement',
    description: 'Check interest rates, penalties, collateral terms, and default conditions.',
    accent: 'from-[#352341] to-[#121a2d]',
  },
  {
    title: 'Service Contract',
    description: 'Understand obligations, deliverables, liabilities, and dispute language.',
    accent: 'from-[#1e2947] to-[#121a2d]',
  },
]

const features = [
  { value: '10K+', label: 'Documents analyzed' },
  { value: '98%', label: 'Accuracy rate' },
  { value: '5K+', label: 'Happy users' },
  { value: '24/7', label: 'AI assistance' },
]

const workflow = [
  {
    step: '01',
    title: 'Upload Your Document',
    description: 'Drop a text-based PDF and let the app organize it instantly.',
  },
  {
    step: '02',
    title: 'Review Key Risks',
    description: 'See clause-by-clause flags, scores, and plain-language summaries.',
  },
  {
    step: '03',
    title: 'Ask Follow-up Questions',
    description: 'Use the AI workspace to ask only about your uploaded document.',
  },
]

export default function Home() {
  return (
    <div className="pb-16 pt-6 sm:pb-20 sm:pt-8">
      <section className="content-wrap">
        <div className="hero-card glow-ring mx-auto max-w-7xl overflow-hidden p-6 sm:p-8 lg:p-10">
          <div className="grid items-center gap-10 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="space-y-6">
              <span className="section-eyebrow">AI Legal Document Assistant</span>
              <div className="space-y-4">
                <h1 className="max-w-3xl text-4xl font-semibold leading-[1.02] text-white sm:text-5xl lg:text-[4rem]">
                  Understand Any Legal Document
                  <span className="text-gradient"> with AI Precision.</span>
                </h1>
                <p className="max-w-2xl text-base leading-8 text-slate-300 sm:text-lg">
                  Upload your rental agreement, employment contract, or loan document. Get plain-language explanations and risk warnings in English and Hindi.
                </p>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row">
                <Link to="/upload" className="btn-primary justify-center px-6 py-3.5 text-sm sm:text-base">
                  Upload a Document
                  <span aria-hidden="true">→</span>
                </Link>
                <Link to="/analysis" className="btn-secondary justify-center px-6 py-3.5 text-sm sm:text-base">
                  View Demo Analysis
                </Link>
              </div>

              <p className="text-sm text-slate-500">No login required to try. 100% free for your first review.</p>
            </div>

            <div className="relative mx-auto flex h-[320px] w-full max-w-[560px] items-center justify-center sm:h-[420px]">
              <div className="absolute inset-x-10 bottom-4 h-14 rounded-full bg-[#5f67ff]/35 blur-3xl" />
              <div className="absolute right-4 top-8 h-16 w-16 rounded-3xl border border-[#8a5cff]/35 bg-[#7c3aed]/10 shadow-[0_0_32px_rgba(124,58,237,0.28)]" />
              <div className="absolute left-8 top-16 h-20 w-20 rounded-full border border-[#f5c26b]/20 bg-[#f5c26b]/8 shadow-[0_0_28px_rgba(245,194,107,0.18)]" />
              <div className="absolute left-0 right-0 top-1/2 h-px bg-gradient-to-r from-transparent via-[#8a5cff]/30 to-transparent" />

              <div className="relative z-10 mx-auto flex w-[72%] max-w-[360px] -rotate-6 flex-col gap-4 rounded-[32px] border border-white/10 bg-[linear-gradient(180deg,rgba(120,102,255,0.25),rgba(10,16,28,0.92))] px-6 py-7 shadow-[0_40px_90px_rgba(0,0,0,0.45)] backdrop-blur-2xl">
                <div className="flex items-center justify-between text-xs uppercase tracking-[0.24em] text-slate-400">
                  <span>Rental agreement</span>
                  <span>AI Scan</span>
                </div>
                <div className="space-y-3">
                  <div className="h-3 w-4/5 rounded-full bg-white/80" />
                  <div className="h-3 w-full rounded-full bg-white/20" />
                  <div className="h-3 w-5/6 rounded-full bg-white/20" />
                  <div className="h-3 w-2/3 rounded-full bg-white/20" />
                </div>
                <div className="rounded-[22px] border border-[#8a5cff]/25 bg-[#0f1630]/80 p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-sm font-medium text-white">Risk Warning</span>
                    <span className="risk-badge-high">High Risk</span>
                  </div>
                  <p className="text-sm leading-6 text-slate-300">
                    Unilateral rent increase without mutual consent and unclear maintenance liability.
                  </p>
                </div>
              </div>

              <div className="absolute bottom-2 left-1/2 h-14 w-48 -translate-x-1/2 rounded-full border border-[#8a5cff]/15 bg-[#090d17] shadow-[0_0_40px_rgba(89,99,255,0.32)]" />

              <div className="absolute bottom-20 left-4 rounded-3xl border border-white/10 bg-[#0f1626]/70 px-4 py-3 backdrop-blur-xl">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Protected</p>
                <p className="text-sm font-medium text-[#f5c26b]">Security Deposit</p>
              </div>

              <div className="absolute right-0 top-1/2 rounded-3xl border border-white/10 bg-[#0f1626]/75 px-4 py-3 backdrop-blur-xl">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Ask AI</p>
                <p className="text-sm font-medium text-white">Break this clause down</p>
              </div>
            </div>
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {features.map((item) => (
              <div key={item.label} className="metric-card rounded-[22px] px-5 py-4">
                <p className="text-3xl font-semibold text-[#f5c26b]">{item.value}</p>
                <p className="mt-1 text-sm text-slate-400">{item.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="content-wrap mt-10 sm:mt-14">
        <div className="mx-auto max-w-7xl">
          <div className="mb-8 text-center">
            <span className="section-eyebrow">What We Analyze</span>
            <h2 className="mt-4 text-3xl font-semibold text-white sm:text-4xl">Our Legal Practice Areas</h2>
            <p className="mx-auto mt-3 max-w-2xl text-sm leading-7 text-slate-400 sm:text-base">
              Comprehensive analysis across all major legal document types, designed to feel clear and trustworthy on every screen size.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {practiceAreas.map((area, index) => (
              <div
                key={area.title}
                className={`group section-card hover-lift relative overflow-hidden rounded-[28px] p-5 ${index === 2 ? 'ring-1 ring-[#8a5cff]/35 shadow-[0_0_45px_rgba(124,58,237,0.22)]' : ''}`}
              >
                <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${area.accent}`} />
                <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-xl text-[#f5c26b]">
                  §
                </div>
                <h3 className="text-xl font-semibold text-white">{area.title}</h3>
                <p className="mt-3 text-sm leading-7 text-slate-400">{area.description}</p>
                <div className="mt-8 flex items-center justify-between text-sm text-slate-500">
                  <span>Review terms</span>
                  <span className="transition group-hover:text-[#f5c26b]">→</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="content-wrap mt-10 sm:mt-14">
        <div className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="section-card rounded-[30px] p-6 sm:p-8">
            <span className="section-eyebrow">How It Works</span>
            <h2 className="mt-4 text-3xl font-semibold text-white">A guided review flow for legal documents.</h2>
            <p className="mt-3 max-w-xl text-sm leading-7 text-slate-400 sm:text-base">
              The visual language from your reference is turned into a real product workflow with clear steps, premium contrast, and responsive spacing.
            </p>

            <div className="mt-8 space-y-4">
              {workflow.map((item) => (
                <div key={item.step} className="info-card rounded-[24px] px-5 py-4">
                  <div className="flex items-start gap-4">
                    <span className="flex h-11 w-11 items-center justify-center rounded-2xl border border-[#f5c26b]/20 bg-[#f5c26b]/10 text-sm font-semibold text-[#f5c26b]">
                      {item.step}
                    </span>
                    <div>
                      <h3 className="text-lg font-medium text-white">{item.title}</h3>
                      <p className="mt-1 text-sm leading-6 text-slate-400">{item.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="section-card relative overflow-hidden rounded-[30px] p-6 sm:p-8">
            <div className="absolute inset-x-0 bottom-0 h-40 bg-[radial-gradient(circle_at_center,rgba(124,58,237,0.22),transparent_70%)]" />
            <div className="relative z-10">
              <span className="section-eyebrow">Product Surface</span>
              <h2 className="mt-4 text-3xl font-semibold text-white">Built to feel like a premium analysis cockpit.</h2>
              <div className="mt-8 grid gap-4 sm:grid-cols-2">
                {[
                  'Clause-by-clause explainers',
                  'Risk warning levels',
                  'Knowledge base and articles',
                  'Responsive auth and 404 states',
                ].map((item) => (
                  <div key={item} className="metric-card rounded-[22px] px-5 py-4 text-sm text-slate-300">
                    {item}
                  </div>
                ))}
              </div>
              <Link to="/upload" className="btn-primary mt-8 justify-center px-6 py-3.5">
                Start With Your Document
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
