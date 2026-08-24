import { useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Card } from '../components/Card'

interface PracticeArea {
  id: string
  title: string
  category: 'Housing' | 'Employment' | 'Finance' | 'Business' | 'Legal'
  description: string
  detailedOverview: string
  accent: string
  icon: string
  keyTerms: string[]
  commonRisks: string[]
}

const practiceAreas: PracticeArea[] = [
  {
    id: 'rental-agreement',
    title: 'Rental Agreement',
    category: 'Housing',
    description: 'Analyze lease terms, rent escalation, security deposit caps, and landlord/tenant notice rules.',
    detailedOverview: 'A legally binding agreement granting temporary residential occupancy rights. Essential for preventing unilateral rent hikes, illegal deposit retention, and abrupt eviction notices under Model Tenancy laws.',
    accent: 'from-[#2a3152] to-[#121a2d]',
    icon: '🏠',
    keyTerms: ['Security Deposit Refund', 'Lock-in Period', 'Notice Period', 'Rent Escalation Cap'],
    commonRisks: ['Lump-sum arbitrary maintenance fees', 'Forfeiture of deposit without receipts'],
  },
  {
    id: 'employment-contract',
    title: 'Employment Contract',
    category: 'Employment',
    description: 'Review probation duration, notice pay in lieu, non-compete validity, IP assignment, and severance.',
    detailedOverview: 'Defines your working terms, CTC breakdown, IP ownership, and exit conditions. Identifies non-compete clauses that are legally void under Section 27 of the Indian Contract Act.',
    accent: 'from-[#241d41] to-[#121a2d]',
    icon: '💼',
    keyTerms: ['Probation & Confirmation', 'Notice Pay', 'Non-Compete Limits', 'IP Ownership'],
    commonRisks: ['Unenforceable post-employment non-compete bonds', 'Unilateral notice period extensions'],
  },
  {
    id: 'loan-agreement',
    title: 'Loan & Debt Agreement',
    category: 'Finance',
    description: 'Check floating vs fixed interest rates, EMI penalties, collateral hypothecation, and foreclosure fees.',
    detailedOverview: 'Establishes debt repayment schedules and collateral security. Highlights illegal foreclosure fees prohibited by RBI guidelines for individual borrowers.',
    accent: 'from-[#352341] to-[#121a2d]',
    icon: '🏦',
    keyTerms: ['Repo Benchmark Rate', 'Foreclosure Fee Waiver', 'Penal Interest Cap', 'Collateral Release'],
    commonRisks: ['Compound interest on delayed EMI', 'Delayed return of property title deeds'],
  },
  {
    id: 'commercial-lease',
    title: 'Commercial Lease Agreement',
    category: 'Housing',
    description: 'Understand fit-out free periods, Common Area Maintenance (CAM), subletting rights, and GST rules.',
    detailedOverview: 'Governs office, retail, or industrial spaces. Analyzes heavy CAM surcharges, fit-out rent waivers, long-term escalation caps, and sub-leasing permissions.',
    accent: 'from-[#1e2947] to-[#121a2d]',
    icon: '🏢',
    keyTerms: ['Fit-out Period', 'CAM Breakdown', 'Subleasing Rights', 'Renewal ROFR'],
    commonRisks: ['Unverified lump-sum CAM billing', 'Lack of municipal commercial usage approvals'],
  },
  {
    id: 'nda',
    title: 'Non-Disclosure Agreement',
    category: 'Legal',
    description: 'Evaluate unilateral vs mutual secrecy, definition of proprietary data, carve-outs, and term limits.',
    detailedOverview: 'Protects business secrets, source code, and client databases. Ensures clear definition of confidential materials with reasonable survival timeframes.',
    accent: 'from-[#3a2046] to-[#121a2d]',
    icon: '🔒',
    keyTerms: ['Scope of Confidentiality', 'Standard Carve-outs', 'Survival Period', 'Data Return'],
    commonRisks: ['Overly broad non-disclosure scope', 'Hidden non-compete clauses embedded in NDA'],
  },
  {
    id: 'service-contract',
    title: 'Service & Freelance Contract',
    category: 'Employment',
    description: 'Define Scope of Work (SOW), payment milestone triggers, revision limits, and liability caps.',
    detailedOverview: 'Protects independent contractors and agencies. Mandates IP transfer only upon 100% full payment settlement and caps total liability to fees received.',
    accent: 'from-[#1a324b] to-[#121a2d]',
    icon: '📋',
    keyTerms: ['SOW Specifications', 'IP Transfer on Payment', 'Late Interest Fees', 'Liability Capping'],
    commonRisks: ['Unbounded revision requests without extra pay', 'Client withholding final payment without rejection notice'],
  },
  {
    id: 'partnership-deed',
    title: 'Partnership & Founder Deed',
    category: 'Business',
    description: 'Vesting schedules, equity allocation, profit sharing ratios, decision deadlock rules, and partner exit.',
    detailedOverview: 'Establishes founder equity vesting over 4 years to prevent early exits with full equity, and provides voting deadlock resolution procedures.',
    accent: 'from-[#2e264a] to-[#121a2d]',
    icon: '🤝',
    keyTerms: ['Founder Reverse Vesting', 'Profit Ratio', 'Deadlock Mediation', 'Buyout Valuation'],
    commonRisks: ['Immediate 100% upfront equity without vesting cliff', 'Paralyzed bank accounts during founder disputes'],
  },
  {
    id: 'sale-deed',
    title: 'Property Sale & Conveyance Deed',
    category: 'Housing',
    description: 'Verify clear legal title warranties, encumbrance certificates, seller indemnity, and possession delivery.',
    detailedOverview: 'Transfers absolute legal title from seller to buyer. Guarantees property is free from mortgages, litigation, or past municipal tax dues.',
    accent: 'from-[#3b2b1a] to-[#121a2d]',
    icon: '📜',
    keyTerms: ['Title Warranty', 'Vendor Indemnity', 'Vacant Possession', 'Stamp Duty Rules'],
    commonRisks: ['Missing mother title deeds', 'Undisclosed inherited property claims'],
  },
  {
    id: 'power-of-attorney',
    title: 'Power of Attorney (PoA)',
    category: 'Legal',
    description: 'Understand Special vs General PoA, NRI consulate attestation, revocability, and sub-registrar registration.',
    detailedOverview: 'Authorizes an agent to act for principal in legal or property matters. Differentiates limited Special PoA from risky blanket General PoA.',
    accent: 'from-[#1e3a34] to-[#121a2d]',
    icon: '⚖️',
    keyTerms: ['Special vs General Authority', 'Express Revocability', 'NRI Adjudication', 'Self-Dealing Prohibition'],
    commonRisks: ['Executing blanket PoA when only one specific task is required', 'Assuming PoA survives principal death'],
  },
  {
    id: 'mou',
    title: 'Memorandum of Understanding',
    category: 'Business',
    description: 'Differentiate non-binding intent from binding exclusivity, confidentiality, and transition timelines.',
    detailedOverview: 'Outlines preliminary business collaboration terms. Ensures non-binding intent statements are explicitly separated from binding confidentiality terms.',
    accent: 'from-[#2c3325] to-[#121a2d]',
    icon: '✍️',
    keyTerms: ['Non-Binding Intent', 'Exclusivity Window', 'Definitive Target Date', 'Cost Sharing'],
    commonRisks: ['Heavy financial penalty clauses in non-binding MoU', 'Indefinite MoU without expiration date'],
  },
  {
    id: 'affidavit',
    title: 'General Affidavit & Sworn Statement',
    category: 'Legal',
    description: 'Notarization rules, stamp paper denomination, sworn fact verification, and perjury liabilities under BNS/IPC.',
    detailedOverview: 'Sworn written statement of facts verified before a Notary Public. Highlights serious criminal liabilities for false statements under perjury laws.',
    accent: 'from-[#342426] to-[#121a2d]',
    icon: '🛡️',
    keyTerms: ['Deponent Sworn Statement', 'Notarial Attestation', 'Stamp Duty Compliance', 'Perjury Warning'],
    commonRisks: ['Signing affidavit outside notary presence', 'Name spelling mismatches with government ID'],
  },
  {
    id: 'vendor-agreement',
    title: 'Vendor & Supply Chain Agreement',
    category: 'Business',
    description: 'SLAs, MSME 45-day payment rules, force majeure conditions, quality inspection, and liquidated damages.',
    detailedOverview: 'Governs supply of goods and raw materials. Enforces statutory 45-day MSME payment rules under Section 15 of MSMED Act 2006.',
    accent: 'from-[#1c2c3e] to-[#121a2d]',
    icon: '🚚',
    keyTerms: ['SLA Quality Inspection', 'MSME 45-Day Payment Rule', 'Force Majeure', 'Liquidated Damages'],
    commonRisks: ['Buyer delaying MSME payments beyond statutory 45-day limit', 'Uncapped delay penalty charges'],
  },
]

const categories = ['All', 'Housing', 'Employment', 'Finance', 'Business', 'Legal'] as const

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
  const navigate = useNavigate()
  const sliderRef = useRef<HTMLDivElement>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>('All')
  const [selectedArea, setSelectedArea] = useState<PracticeArea | null>(null)

  const filteredAreas = practiceAreas.filter(
    (area) => selectedCategory === 'All' || area.category === selectedCategory
  )

  const scrollLeft = () => {
    if (sliderRef.current) {
      sliderRef.current.scrollBy({ left: -340, behavior: 'smooth' })
    }
  }

  const scrollRight = () => {
    if (sliderRef.current) {
      sliderRef.current.scrollBy({ left: 340, behavior: 'smooth' })
    }
  }

  return (
    <div className="pb-16 pt-6 sm:pb-20 sm:pt-6">
      {/* Hero Section */}
      <section className="content-wrap">
        <Card variant="hero" className="mx-auto max-w-7xl overflow-hidden rounded-[32px] p-6 sm:p-8 lg:p-10">
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
              <Card key={item.label} variant="metric" className="rounded-[22px] px-5 py-4">
                <p className="text-3xl font-semibold text-[#f5c26b]">{item.value}</p>
                <p className="mt-1 text-sm text-slate-400">{item.label}</p>
              </Card>
            ))}
          </div>
        </Card>
      </section>

      {/* Practice Areas Slider Section */}
      <section className="content-wrap mt-10 sm:mt-14">
        <div className="mx-auto max-w-7xl">
          
          {/* Header & Controls */}
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between mb-6">
            <div>
              <span className="section-eyebrow">What We Analyze</span>
              <h2 className="mt-3 text-3xl font-semibold text-white sm:text-4xl">Our Legal Practice Areas</h2>
              <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-400 sm:text-base">
                Comprehensive analysis across 12 major Indian legal document types. Swipe or use controls to explore.
              </p>
            </div>

            {/* Slider Arrow Controls */}
            <div className="flex items-center gap-3 shrink-0">
              <button
                type="button"
                onClick={scrollLeft}
                aria-label="Scroll left"
                className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/12 bg-white/5 text-slate-200 transition hover:border-[#f5c26b]/30 hover:bg-white/10 hover:text-white"
              >
                ←
              </button>
              <button
                type="button"
                onClick={scrollRight}
                aria-label="Scroll right"
                className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/12 bg-white/5 text-slate-200 transition hover:border-[#f5c26b]/30 hover:bg-white/10 hover:text-white"
              >
                →
              </button>
            </div>
          </div>

          {/* Category Filter Pills */}
          <div className="mb-6 flex flex-wrap items-center gap-2">
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={`rounded-full px-4 py-2 text-xs font-medium transition-all duration-200 ${
                  selectedCategory === cat
                    ? 'bg-[#f5c26b] text-slate-950 font-semibold shadow-[0_0_18px_rgba(245,194,107,0.3)]'
                    : 'border border-white/10 bg-white/[0.03] text-slate-300 hover:border-white/20 hover:text-white'
                }`}
              >
                {cat === 'All' ? 'All Document Types' : cat}
              </button>
            ))}
          </div>

          {/* Horizontal Card Slider */}
          <div
            ref={sliderRef}
            className="flex items-stretch gap-5 overflow-x-auto pb-6 pt-2 snap-x snap-mandatory scrollbar-none scroll-smooth"
            style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
          >
            {filteredAreas.map((area, index) => (
              <div
                key={area.id}
                className="w-[290px] sm:w-[330px] shrink-0 snap-start"
              >
                <Card
                  variant="section"
                  hoverLift
                  glow={index === 0 || index === 2}
                  onClick={() => setSelectedArea(area)}
                  className="group relative flex h-full flex-col justify-between overflow-hidden rounded-[28px] p-5 cursor-pointer"
                >
                  <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${area.accent}`} />
                  <div>
                    <div className="mb-5 flex items-center justify-between">
                      <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-2xl shadow-inner">
                        {area.icon}
                      </div>
                      <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                        {area.category}
                      </span>
                    </div>
                    <h3 className="text-xl font-semibold text-white transition-colors group-hover:text-[#f5c26b]">
                      {area.title}
                    </h3>
                    <p className="mt-3 text-sm leading-7 text-slate-400">
                      {area.description}
                    </p>

                    <div className="mt-4 flex flex-wrap gap-1.5">
                      {area.keyTerms.slice(0, 3).map((term) => (
                        <span key={term} className="rounded-md border border-white/8 bg-white/[0.02] px-2 py-0.5 text-[11px] text-slate-400">
                          • {term}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="mt-8 flex items-center justify-between border-t border-white/8 pt-4 text-sm text-slate-400">
                    <span className="text-xs font-semibold text-[#f5c26b]">Review terms</span>
                    <span className="transition-transform group-hover:translate-x-1 group-hover:text-[#f5c26b]">→</span>
                  </div>
                </Card>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Practice Area Detail Modal */}
      {selectedArea && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <Card variant="section" className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-[32px] p-6 sm:p-8 relative">
            <button
              type="button"
              onClick={() => setSelectedArea(null)}
              className="absolute top-6 right-6 flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-white/5 text-slate-400 hover:text-white"
            >
              ✕
            </button>

            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-3xl">
                {selectedArea.icon}
              </div>
              <div>
                <span className="text-xs uppercase tracking-[0.2em] font-semibold text-[#f5c26b]">{selectedArea.category}</span>
                <h2 className="text-2xl font-bold text-white mt-1">{selectedArea.title}</h2>
              </div>
            </div>

            <p className="mt-4 text-sm leading-7 text-slate-300">
              {selectedArea.detailedOverview}
            </p>

            <div className="mt-6 space-y-4 border-t border-white/10 pt-6">
              <h4 className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Core Clauses Analyzed by SmartLegal AI</h4>
              <div className="grid gap-2.5 sm:grid-cols-2">
                {selectedArea.keyTerms.map((term) => (
                  <div key={term} className="metric-card rounded-2xl p-3.5 text-xs font-medium text-slate-200 flex items-center gap-2">
                    <span className="text-[#f5c26b]">🔍</span> {term}
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-6 rounded-2xl border border-[#fb7185]/20 bg-[#2a1320]/40 p-4">
              <h4 className="text-xs font-semibold uppercase tracking-[0.18em] text-[#fecdd3] mb-2">High Risk Traps Flagged in this Agreement</h4>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {selectedArea.commonRisks.map((risk, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-[#fb7185]">⚠️</span>
                    <span>{risk}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-8 flex flex-wrap justify-end gap-3">
              <button
                type="button"
                onClick={() => {
                  setSelectedArea(null)
                  window.scrollTo(0, 0)
                  navigate('/compare')
                }}
                className="btn-secondary px-5 py-2.5 text-xs"
              >
                Read Full Knowledge Base Article →
              </button>
              <button
                type="button"
                onClick={() => {
                  setSelectedArea(null)
                  window.scrollTo(0, 0)
                  navigate('/upload')
                }}
                className="btn-primary px-5 py-2.5 text-xs"
              >
                Upload {selectedArea.title} →
              </button>
            </div>
          </Card>
        </div>
      )}

      {/* How it Works & Product Surface */}
      <section className="content-wrap mt-10 sm:mt-14">
        <div className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <Card variant="section" className="rounded-[30px] p-6 sm:p-8">
            <span className="section-eyebrow">How It Works</span>
            <h2 className="mt-4 text-3xl font-semibold text-white">A guided review flow for legal documents.</h2>
            <p className="mt-3 max-w-xl text-sm leading-7 text-slate-400 sm:text-base">
              The visual language from your reference is turned into a real product workflow with clear steps, premium contrast, and responsive spacing.
            </p>

            <div className="mt-8 space-y-4">
              {workflow.map((item) => (
                <Card key={item.step} variant="info" className="rounded-[24px] px-5 py-4">
                  <div className="flex items-start gap-4">
                    <span className="flex h-11 w-11 items-center justify-center rounded-2xl border border-[#f5c26b]/20 bg-[#f5c26b]/10 text-sm font-semibold text-[#f5c26b]">
                      {item.step}
                    </span>
                    <div>
                      <h3 className="text-lg font-medium text-white">{item.title}</h3>
                      <p className="mt-1 text-sm leading-6 text-slate-400">{item.description}</p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </Card>

          <Card variant="section" className="relative overflow-hidden rounded-[30px] p-6 sm:p-8">
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
                  <Card key={item} variant="metric" className="rounded-[22px] px-5 py-4 text-sm text-slate-300">
                    {item}
                  </Card>
                ))}
              </div>
              <Link to="/upload" className="btn-primary mt-8 justify-center px-6 py-3.5">
                Start With Your Document
              </Link>
            </div>
          </Card>
        </div>
      </section>
    </div>
  )
}
