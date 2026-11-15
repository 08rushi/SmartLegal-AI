import { useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Card } from '../components/Card'
import { LanguageSwitcher } from '../components/ui/LanguageSwitcher'
import { Modal } from '../components/ui/Modal'
import { SpeakButton } from '../components/ui/SpeakButton'
import { SpeechNotice } from '../components/ui/SpeechNotice'

type Category = 'Housing' | 'Employment' | 'Finance' | 'Business' | 'Legal'

interface PracticeArea {
  id: string
  category: Category
  accent: string
  icon: string
}

const practiceAreas: PracticeArea[] = [
  { id: 'rental-agreement', category: 'Housing', accent: 'from-[#2a3152] to-[#121a2d]', icon: '🏠' },
  { id: 'employment-contract', category: 'Employment', accent: 'from-[#241d41] to-[#121a2d]', icon: '💼' },
  { id: 'loan-agreement', category: 'Finance', accent: 'from-[#352341] to-[#121a2d]', icon: '🏦' },
  { id: 'commercial-lease', category: 'Housing', accent: 'from-[#1e2947] to-[#121a2d]', icon: '🏢' },
  { id: 'nda', category: 'Legal', accent: 'from-[#3a2046] to-[#121a2d]', icon: '🔒' },
  { id: 'service-contract', category: 'Employment', accent: 'from-[#1a324b] to-[#121a2d]', icon: '📋' },
  { id: 'partnership-deed', category: 'Business', accent: 'from-[#2e264a] to-[#121a2d]', icon: '🤝' },
  { id: 'sale-deed', category: 'Housing', accent: 'from-[#3b2b1a] to-[#121a2d]', icon: '📜' },
  { id: 'power-of-attorney', category: 'Legal', accent: 'from-[#1e3a34] to-[#121a2d]', icon: '⚖️' },
  { id: 'mou', category: 'Business', accent: 'from-[#2c3325] to-[#121a2d]', icon: '✍️' },
  { id: 'affidavit', category: 'Legal', accent: 'from-[#342426] to-[#121a2d]', icon: '🛡️' },
  { id: 'vendor-agreement', category: 'Business', accent: 'from-[#1c2c3e] to-[#121a2d]', icon: '🚚' },
]

const categories = ['All', 'Housing', 'Employment', 'Finance', 'Business', 'Legal'] as const

const FEATURE_KEYS = ['plain', 'risk', 'languages', 'ask'] as const
const WORKFLOW = [
  { step: '01', key: 'upload' },
  { step: '02', key: 'review' },
  { step: '03', key: 'ask' },
] as const
const SURFACE_KEYS = ['clauses', 'risk', 'kb'] as const

const TERM_COUNT = 4
const RISK_COUNT = 2
const indexes = (n: number) => Array.from({ length: n }, (_, i) => i)

export default function Home() {
  const { t } = useTranslation('home')
  const navigate = useNavigate()
  const sliderRef = useRef<HTMLDivElement>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>('All')
  const [selectedArea, setSelectedArea] = useState<PracticeArea | null>(null)
  const [hasSpoken, setHasSpoken] = useState(false)

  const filteredAreas = practiceAreas.filter((area) => selectedCategory === 'All' || area.category === selectedCategory)

  const scrollBy = (left: number) => sliderRef.current?.scrollBy({ left, behavior: 'smooth' })
  const welcome = `${t('hero.titleMain')}${t('hero.titleAccent')}. ${t('hero.body')}`

  return (
    <div className="pb-16 pt-6 sm:pb-20 sm:pt-6">
      {/* Hero Section */}
      <section className="content-wrap" aria-labelledby="home-title">
        <Card variant="hero" className="mx-auto max-w-7xl overflow-hidden rounded-[32px] p-6 sm:p-8 lg:p-10">
          <div className="grid items-center gap-10 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="space-y-6">
              <span className="section-eyebrow">{t('hero.eyebrow')}</span>
              <div className="space-y-4">
                <h1
                  id="home-title"
                  className="max-w-3xl text-4xl font-semibold leading-[1.02] text-white sm:text-5xl lg:text-[4rem]"
                >
                  {t('hero.titleMain')}
                  <span className="text-gradient">{t('hero.titleAccent')}</span>
                </h1>
                <p className="max-w-2xl text-base leading-8 text-slate-300 sm:text-lg">{t('hero.body')}</p>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <Link to="/upload" className="btn-primary justify-center px-6 py-3.5 text-sm sm:text-base">
                  {t('hero.upload')}
                  <span aria-hidden="true">→</span>
                </Link>
                <Link to="/analysis" className="btn-secondary justify-center px-6 py-3.5 text-sm sm:text-base">
                  {t('hero.demo')}
                </Link>
                <SpeakButton text={welcome} label={t('hero.titleMain')} onSpeak={() => setHasSpoken(true)} />
              </div>
              <SpeechNotice show={hasSpoken} />

              {/* Language chooser */}
              <div className="space-y-2 pt-2">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#f5c26b]">{t('language.title')}</p>
                <LanguageSwitcher variant="full" />
                <p className="text-xs text-slate-400">{t('language.hint')}</p>
              </div>
            </div>

            <div className="relative mx-auto flex h-[320px] w-full max-w-[560px] items-center justify-center sm:h-[420px]" aria-hidden="true">
              <div className="absolute inset-x-10 bottom-4 h-14 rounded-full bg-[#5f67ff]/35 blur-3xl" />
              <div className="absolute right-4 top-8 h-16 w-16 rounded-3xl border border-[#8a5cff]/35 bg-[#7c3aed]/10 shadow-[0_0_32px_rgba(124,58,237,0.28)]" />
              <div className="absolute left-8 top-16 h-20 w-20 rounded-full border border-[#f5c26b]/20 bg-[#f5c26b]/8 shadow-[0_0_28px_rgba(245,194,107,0.18)]" />
              <div className="absolute left-0 right-0 top-1/2 h-px bg-gradient-to-r from-transparent via-[#8a5cff]/30 to-transparent" />

              <div className="relative z-10 mx-auto flex w-[72%] max-w-[360px] -rotate-6 flex-col gap-4 rounded-[32px] border border-white/10 bg-[linear-gradient(180deg,rgba(120,102,255,0.25),rgba(10,16,28,0.92))] px-6 py-7 shadow-[0_40px_90px_rgba(0,0,0,0.45)] backdrop-blur-2xl">
                <div className="flex items-center justify-between text-xs uppercase tracking-[0.24em] text-slate-400">
                  <span>{t('hero.cardTop')}</span>
                  <span>{t('hero.cardScan')}</span>
                </div>
                <div className="space-y-3">
                  <div className="h-3 w-4/5 rounded-full bg-white/80" />
                  <div className="h-3 w-full rounded-full bg-white/20" />
                  <div className="h-3 w-5/6 rounded-full bg-white/20" />
                  <div className="h-3 w-2/3 rounded-full bg-white/20" />
                </div>
                <div className="rounded-[22px] border border-[#8a5cff]/25 bg-[#0f1630]/80 p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-sm font-medium text-white">{t('hero.riskWarning')}</span>
                    <span className="risk-badge-high">{t('hero.highRisk')}</span>
                  </div>
                  <p className="text-sm leading-6 text-slate-300">{t('hero.riskBody')}</p>
                </div>
              </div>

              <div className="absolute bottom-2 left-1/2 h-14 w-48 -translate-x-1/2 rounded-full border border-[#8a5cff]/15 bg-[#090d17] shadow-[0_0_40px_rgba(89,99,255,0.32)]" />

              <div className="absolute bottom-20 left-4 rounded-3xl border border-white/10 bg-[#0f1626]/70 px-4 py-3 backdrop-blur-xl">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{t('hero.protected')}</p>
                <p className="text-sm font-medium text-[#f5c26b]">{t('hero.securityDeposit')}</p>
              </div>

              <div className="absolute right-0 top-1/2 rounded-3xl border border-white/10 bg-[#0f1626]/75 px-4 py-3 backdrop-blur-xl">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{t('hero.askAi')}</p>
                <p className="text-sm font-medium text-white">{t('hero.askAiSample')}</p>
              </div>
            </div>
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {FEATURE_KEYS.map((key) => (
              <Card key={key} variant="metric" className="rounded-[22px] px-5 py-4">
                <p className="text-2xl font-semibold text-[#f5c26b]">{t(`features.${key}.value`)}</p>
                <p className="mt-1 text-sm text-slate-400">{t(`features.${key}.label`)}</p>
              </Card>
            ))}
          </div>
        </Card>
      </section>

      {/* Practice Areas Slider Section */}
      <section className="content-wrap mt-10 sm:mt-14" aria-labelledby="home-papers">
        <div className="mx-auto max-w-7xl">
          <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <span className="section-eyebrow">{t('areas.eyebrow')}</span>
              <h2 id="home-papers" className="mt-3 text-3xl font-semibold text-white sm:text-4xl">
                {t('areas.title')}
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-400 sm:text-base">{t('areas.body')}</p>
            </div>

            <div className="flex shrink-0 items-center gap-3">
              <button
                type="button"
                onClick={() => scrollBy(-340)}
                aria-label={t('areas.scrollLeft')}
                className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/12 bg-white/5 text-slate-200 transition hover:border-[#f5c26b]/30 hover:bg-white/10 hover:text-white"
              >
                <span aria-hidden="true">←</span>
              </button>
              <button
                type="button"
                onClick={() => scrollBy(340)}
                aria-label={t('areas.scrollRight')}
                className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/12 bg-white/5 text-slate-200 transition hover:border-[#f5c26b]/30 hover:bg-white/10 hover:text-white"
              >
                <span aria-hidden="true">→</span>
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
                aria-pressed={selectedCategory === cat}
                className={`rounded-full px-4 py-2 text-xs font-medium transition-all duration-200 ${
                  selectedCategory === cat
                    ? 'bg-[#f5c26b] font-semibold text-slate-950 shadow-[0_0_18px_rgba(245,194,107,0.3)]'
                    : 'border border-white/10 bg-white/[0.03] text-slate-300 hover:border-white/20 hover:text-white'
                }`}
              >
                {cat === 'All' ? t('areas.all') : t(`areas.categories.${cat}`)}
              </button>
            ))}
          </div>

          {/* Horizontal Card Slider */}
          <div
            ref={sliderRef}
            className="scrollbar-none flex snap-x snap-mandatory items-stretch gap-5 overflow-x-auto scroll-smooth pb-6 pt-2"
            style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
          >
            {filteredAreas.map((area, index) => (
              <div key={area.id} className="w-[290px] shrink-0 snap-start sm:w-[330px]">
                <Card
                  variant="section"
                  hoverLift
                  glow={index === 0 || index === 2}
                  className="group relative flex h-full flex-col justify-between overflow-hidden rounded-[28px] p-5"
                >
                  <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${area.accent}`} />
                  <button
                    type="button"
                    onClick={() => setSelectedArea(area)}
                    aria-haspopup="dialog"
                    className="flex h-full flex-col justify-between text-left"
                  >
                    <span className="block">
                      <span className="mb-5 flex items-center justify-between">
                        <span className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-2xl shadow-inner" aria-hidden="true">
                          {area.icon}
                        </span>
                        <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                          {t(`areas.categories.${area.category}`)}
                        </span>
                      </span>
                      <span className="block text-xl font-semibold text-white transition-colors group-hover:text-[#f5c26b]">
                        {t(`areas.items.${area.id}.title`)}
                      </span>
                      <span className="mt-3 block text-sm leading-7 text-slate-400">
                        {t(`areas.items.${area.id}.description`)}
                      </span>
                      <span className="mt-4 flex flex-wrap gap-1.5">
                        {indexes(3).map((i) => (
                          <span key={i} className="rounded-md border border-white/8 bg-white/[0.02] px-2 py-0.5 text-[11px] text-slate-400">
                            • {t(`areas.items.${area.id}.terms.${i}`)}
                          </span>
                        ))}
                      </span>
                    </span>
                    <span className="mt-8 flex w-full items-center justify-between border-t border-white/8 pt-4 text-sm text-slate-400">
                      <span className="text-xs font-semibold text-[#f5c26b]">{t('areas.reviewTerms')}</span>
                      <span aria-hidden="true" className="transition-transform group-hover:translate-x-1 group-hover:text-[#f5c26b]">
                        →
                      </span>
                    </span>
                  </button>
                </Card>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Practice Area Detail dialog */}
      <Modal
        isOpen={selectedArea !== null}
        onClose={() => setSelectedArea(null)}
        labelledBy="home-area-title"
        look="card"
        size="md"
      >
        {selectedArea && (
          <div>
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-3xl" aria-hidden="true">
                {selectedArea.icon}
              </div>
              <div>
                <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[#f5c26b]">
                  {t(`areas.categories.${selectedArea.category}`)}
                </span>
                <h2 id="home-area-title" className="mt-1 text-2xl font-bold text-white">
                  {t(`areas.items.${selectedArea.id}.title`)}
                </h2>
              </div>
            </div>
            <p className="mt-4 text-sm leading-7 text-slate-300">{t(`areas.items.${selectedArea.id}.overview`)}</p>

            <div className="mt-6 space-y-4 border-t border-white/10 pt-6">
              <h3 className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{t('modal.coreClauses')}</h3>
              <ul className="grid gap-2.5 sm:grid-cols-2">
                {indexes(TERM_COUNT).map((i) => (
                  <li key={i} className="metric-card flex items-center gap-2 rounded-2xl p-3.5 text-xs font-medium text-slate-200">
                    <span className="text-[#f5c26b]" aria-hidden="true">
                      🔍
                    </span>
                    {t(`areas.items.${selectedArea.id}.terms.${i}`)}
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-6 rounded-2xl border border-[#fb7185]/20 bg-[#2a1320]/40 p-4">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-[#fecdd3]">{t('modal.riskTraps')}</h3>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {indexes(RISK_COUNT).map((i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-[#fb7185]" aria-hidden="true">
                      ⚠️
                    </span>
                    <span>{t(`areas.items.${selectedArea.id}.risks.${i}`)}</span>
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
                  navigate('/knowledge-base')
                }}
                className="btn-secondary px-5 py-2.5 text-xs"
              >
                {t('modal.readArticle')}
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
                {t('modal.uploadType', { title: t(`areas.items.${selectedArea.id}.title`) })}
              </button>
            </div>
          </div>
        )}
      </Modal>

      {/* How it Works & Product Surface */}
      <section className="content-wrap mt-10 sm:mt-14">
        <div className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <Card variant="section" className="rounded-[30px] p-6 sm:p-8">
            <span className="section-eyebrow">{t('how.eyebrow')}</span>
            <h2 className="mt-4 text-3xl font-semibold text-white">{t('how.title')}</h2>
            <p className="mt-3 max-w-xl text-sm leading-7 text-slate-400 sm:text-base">{t('how.body')}</p>

            <ol className="mt-8 space-y-4">
              {WORKFLOW.map((item) => (
                <li key={item.step}>
                  <Card variant="info" className="rounded-[24px] px-5 py-4">
                    <div className="flex items-start gap-4">
                      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-[#f5c26b]/20 bg-[#f5c26b]/10 text-sm font-semibold text-[#f5c26b]">
                        {item.step}
                      </span>
                      <div>
                        <h3 className="text-lg font-medium text-white">{t(`how.steps.${item.key}.title`)}</h3>
                        <p className="mt-1 text-sm leading-6 text-slate-400">{t(`how.steps.${item.key}.description`)}</p>
                      </div>
                    </div>
                  </Card>
                </li>
              ))}
            </ol>
          </Card>

          <Card variant="section" className="relative overflow-hidden rounded-[30px] p-6 sm:p-8">
            <div className="absolute inset-x-0 bottom-0 h-40 bg-[radial-gradient(circle_at_center,rgba(124,58,237,0.22),transparent_70%)]" aria-hidden="true" />
            <div className="relative z-10">
              <span className="section-eyebrow">{t('surface.eyebrow')}</span>
              <h2 className="mt-4 text-3xl font-semibold text-white">{t('surface.title')}</h2>
              <ul className="mt-8 grid gap-4 sm:grid-cols-2">
                {SURFACE_KEYS.map((key) => (
                  <li key={key}>
                    <Card variant="metric" className="rounded-[22px] px-5 py-4 text-sm text-slate-300">
                      {t(`surface.items.${key}`)}
                    </Card>
                  </li>
                ))}
                <li>
                  <Card variant="metric" className="rounded-[22px] px-5 py-4 text-sm text-slate-300">
                    {t('honest')}
                  </Card>
                </li>
              </ul>
              <Link to="/upload" className="btn-primary mt-8 justify-center px-6 py-3.5">
                {t('surface.cta')}
              </Link>
            </div>
          </Card>
        </div>
      </section>
    </div>
  )
}
