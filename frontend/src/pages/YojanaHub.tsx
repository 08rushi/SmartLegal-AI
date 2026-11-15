import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { fetchYojanaSchemes, fetchYojanaBlogs } from '../store/yojanaSlice'
import { YojanaDynamicForm } from '../components/YojanaDynamicForm'
import type { YojanaScheme } from '../types'


const CATEGORIES = ['ALL', 'Agriculture', 'Healthcare', 'Finance', 'Women', 'Education', 'Housing']
const STATES = ['ALL', 'Maharashtra', 'Madhya Pradesh', 'Uttar Pradesh', 'Delhi', 'Gujarat', 'Karnataka']

const SCHEME_IMAGES: Record<string, string> = {
  PM_KISAN: '/illustrations/pm_kisan_banner.jpg',
  ABHA_CARD: '/illustrations/abha_card_banner.jpg',
  AYUSHMAN_BHARAT: '/illustrations/ayushman_bharat_banner.jpg',
  PM_JANDHAN: '/illustrations/jan_dhan_banner.jpg',
  LADLI_BEHNA_MP: '/illustrations/ladli_behna_banner.jpg',
  MJPJAY_MH: '/illustrations/ayushman_bharat_banner.jpg',
}

function getSchemeBanner(schemeCode?: string, category?: string): string {
  if (schemeCode && SCHEME_IMAGES[schemeCode]) {
    return SCHEME_IMAGES[schemeCode]
  }
  const cat = (category || '').toLowerCase()
  if (cat.includes('agri')) return '/illustrations/pm_kisan_banner.jpg'
  if (cat.includes('health')) return '/illustrations/ayushman_bharat_banner.jpg'
  if (cat.includes('women')) return '/illustrations/ladli_behna_banner.jpg'
  if (cat.includes('fin')) return '/illustrations/jan_dhan_banner.jpg'
  return '/illustrations/abha_card_banner.jpg'
}


/**
 * Plain-language summary in the active language.
 * TODO(i18n-content): the backend will return summaries/titles/benefits in the requested `lang`
 * (X-Lang header / `lang` query param). Until then Hindi falls back to summary_hindi, and Marathi
 * uses an optional summary_marathi if present, else the Hindi (Devanagari) text, else English.
 */
function schemeSummary(sch: YojanaScheme, lang: string): string {
  const extra = sch as unknown as Record<string, string | undefined>
  if (lang === 'mr') return extra.summary_marathi || extra.summary_mr || sch.summary_hindi || sch.summary_english
  if (lang === 'hi') return sch.summary_hindi || sch.summary_english
  return sch.summary_english
}

export const YojanaHub: React.FC = () => {
  const { t, i18n } = useTranslation('yojana')
  const lang = i18n.language.slice(0, 2)
  const locale = `${lang}-IN`
  const dispatch = useAppDispatch()
  const { schemes, matchedResults, blogs } = useAppSelector((s) => s.yojana)


  const [selectedCategory, setSelectedCategory] = useState('ALL')
  const [selectedState, setSelectedState] = useState('ALL')
  const [activeTab, setActiveTab] = useState<'schemes' | 'matcher' | 'blogs'>('schemes')

  useEffect(() => {
    // `lang` is sent as a query param too (backend may ignore it for now; X-Lang header is always sent).
    const filters = { category: selectedCategory, state: selectedState, lang }
    dispatch(fetchYojanaSchemes(filters))
    dispatch(fetchYojanaBlogs())
  }, [dispatch, selectedCategory, selectedState, lang])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Banner Hero */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-900/40 via-slate-900 to-slate-900 border border-slate-800 p-8 sm:p-10 shadow-2xl">
          <div className="relative z-10 max-w-3xl space-y-4">
            <span className="inline-block px-3 py-1 bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs font-semibold rounded-full">
              {t('hub.badge')}
            </span>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              {t('hub.title')}
            </h1>
            <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
              {t('hub.intro')}
            </p>
            <div className="flex flex-wrap gap-3 pt-2">
              <button
                onClick={() => setActiveTab('matcher')}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg transition-all"
              >
                {t('hub.ctaTest')}
              </button>
              <button
                onClick={() => setActiveTab('blogs')}
                className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs rounded-xl border border-slate-700 transition-all"
              >
                {t('hub.ctaGuides')}
              </button>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-800 gap-6">
          <button
            onClick={() => setActiveTab('schemes')}
            className={`pb-3 text-sm font-semibold border-b-2 transition-all ${
              activeTab === 'schemes'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {t('hub.tabs.schemes', { count: schemes.length })}
          </button>
          <button
            onClick={() => setActiveTab('matcher')}
            className={`pb-3 text-sm font-semibold border-b-2 transition-all ${
              activeTab === 'matcher'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {matchedResults.length > 0
              ? t('hub.tabs.matcherCount', { count: matchedResults.length })
              : t('hub.tabs.matcher')}
          </button>
          <button
            onClick={() => setActiveTab('blogs')}
            className={`pb-3 text-sm font-semibold border-b-2 transition-all ${
              activeTab === 'blogs'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {t('hub.tabs.blogs', { count: blogs.length })}
          </button>
        </div>

        {/* TAB 1: ALL ACTIVE SCHEMES */}
        {activeTab === 'schemes' && (
          <div className="space-y-6">
            {/* Filters */}
            <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/60 p-4 rounded-2xl border border-slate-800">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-semibold text-slate-400">{t('hub.filters.category')}</span>
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                    className={`px-3 py-1.5 text-xs rounded-xl font-medium transition-all ${
                      selectedCategory === cat
                        ? 'bg-indigo-600 text-white'
                        : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
                    }`}
                  >
                    {t(`categories.${cat}`, { defaultValue: cat })}
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-400">{t('hub.filters.state')}</span>
                <select
                  value={selectedState}
                  onChange={(e) => setSelectedState(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none"
                >
                  {STATES.map((st) => (
                    <option key={st} value={st}>
                      {t(`states.${st}`, { defaultValue: st })}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Scheme Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {schemes.length === 0 && (
                <p className="col-span-full py-8 text-center text-sm text-slate-400">{t('hub.noSchemes')}</p>
              )}
              {schemes.map((sch) => {
                const imgBanner = getSchemeBanner(sch.scheme_code, sch.category)
                return (
                  <div
                    key={sch.id}
                    className="bg-slate-900/80 border border-slate-800 hover:border-indigo-500/50 rounded-2xl overflow-hidden transition-all shadow-xl hover:shadow-indigo-500/10 flex flex-col justify-between group"
                  >
                    <div>
                      {/* Image Banner Header */}
                      <div className="relative h-44 w-full overflow-hidden bg-slate-950">
                        <img
                          src={imgBanner}
                          alt={sch.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/40 to-transparent" />
                        <div className="absolute top-3 left-3 right-3 flex items-center justify-between">
                          <span className="px-2.5 py-1 bg-slate-950/80 backdrop-blur-md text-indigo-300 border border-indigo-500/30 text-[10px] font-bold uppercase rounded-lg shadow-md">
                            {t(`levels.${(sch.government_level || '').toLowerCase()}`, { defaultValue: sch.government_level })} •{' '}
                            {t(`states.${sch.state_name}`, { defaultValue: sch.state_name })}
                          </span>
                          <span className="px-2.5 py-1 bg-indigo-600/90 text-white text-[10px] font-bold rounded-lg shadow-md">
                            {t(`categories.${sch.category}`, { defaultValue: sch.category })}
                          </span>
                        </div>
                      </div>

                      <div className="p-5 space-y-3">
                        <h3 className="text-base font-extrabold text-white group-hover:text-indigo-300 transition-colors">
                          {sch.title}
                        </h3>

                        {/* Plain Language Bilingual Summary */}
                        <div className="space-y-1">
                          <p className="text-xs text-slate-300 leading-relaxed line-clamp-2">
                            {schemeSummary(sch, lang)}
                          </p>
                          {sch.summary_hindi && sch.summary_hindi !== schemeSummary(sch, lang) && (
                            <p className="text-[11px] text-amber-300/90 font-sans leading-relaxed line-clamp-1 bg-amber-950/30 px-2 py-1 rounded-md border border-amber-800/30">
                              🇮🇳 {sch.summary_hindi}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="p-5 pt-0 space-y-4">
                      <div className="border-t border-slate-800/80 pt-3 space-y-2">
                        <span className="text-[11px] font-semibold text-slate-400 block uppercase tracking-wider">
                          {t('hub.benefitsTitle')}
                        </span>
                        <ul className="text-xs text-slate-200 space-y-1.5">
                          {sch.benefits.slice(0, 2).map((b, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <span className="text-emerald-400 text-sm font-bold">✓</span>
                              <span>{b}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-slate-800/50">
                        <a
                          href={sch.official_portal_url}
                          target="_blank"
                          rel="noreferrer"
                          className="px-3 py-1.5 bg-slate-950 hover:bg-slate-800 text-emerald-400 border border-emerald-800/50 text-xs font-semibold rounded-xl transition-all flex items-center gap-1.5"
                        >
                          <span>{t('hub.officialWebsite')}</span>
                          <span>🔗</span>
                        </a>
                        <button
                          onClick={() => setActiveTab('matcher')}
                          className="px-3 py-1.5 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white text-xs font-semibold rounded-xl shadow-md transition-all"
                        >
                          {t('hub.checkMatch')}
                        </button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}


        {/* TAB 2: ELIGIBILITY MATCHER */}
        {activeTab === 'matcher' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-5">
              <YojanaDynamicForm onMatched={() => setActiveTab('matcher')} />
            </div>

            <div className="lg:col-span-7 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white">{t('hub.matcher.resultsTitle')}</h3>
                <span className="text-xs text-slate-400">
                  {matchedResults.length > 0
                    ? t('hub.matcher.evaluated', { count: matchedResults.length })
                    : t('hub.matcher.fillForm')}
                </span>
              </div>

              {matchedResults.length === 0 ? (
                <div className="bg-slate-900/40 border border-slate-800/60 rounded-2xl p-8 text-center space-y-3">
                  <span className="text-3xl">📋</span>
                  <h4 className="text-sm font-semibold text-slate-300">{t('hub.matcher.emptyTitle')}</h4>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto">
                    {t('hub.matcher.emptyBody')}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {matchedResults.map((m, idx) => (
                    <div
                      key={idx}
                      className={`p-5 rounded-2xl border transition-all ${
                        m.status === 'eligible'
                          ? 'bg-emerald-950/20 border-emerald-800/40'
                          : m.status === 'partial'
                          ? 'bg-amber-950/20 border-amber-800/40'
                          : 'bg-slate-900/40 border-slate-800/60'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span
                              className={`px-2.5 py-0.5 text-[10px] font-bold rounded-md uppercase ${
                                m.status === 'eligible'
                                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                  : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                              }`}
                            >
                              {t('hub.matcher.matchBadge', {
                                score: m.match_score,
                                status: t(`status.${m.status}`, { defaultValue: m.status }),
                              })}
                            </span>
                            <span className="text-xs text-slate-400 font-medium">
                              {t(`levels.${(m.scheme.government_level || '').toLowerCase()}`, {
                                defaultValue: m.scheme.government_level,
                              })}{' '}
                              • {t(`states.${m.scheme.state_name}`, { defaultValue: m.scheme.state_name })}
                            </span>
                          </div>
                          <h4 className="text-base font-bold text-white">{m.scheme.title}</h4>
                        </div>

                        <a
                          href={m.official_portal_url}
                          target="_blank"
                          rel="noreferrer"
                          className="px-3 py-1.5 bg-indigo-600 text-white text-xs font-semibold rounded-lg hover:bg-indigo-500 transition-all flex-shrink-0"
                        >
                          {t('hub.matcher.applyOfficial')}
                        </a>
                      </div>

                      {/* Gap Analysis */}
                      {m.gap_analysis.length > 0 && (
                        <div className="mt-3 p-3 bg-slate-950/80 rounded-xl border border-slate-800 space-y-1">
                          <span className="text-[11px] font-semibold text-amber-400 block">{t('hub.matcher.gapTitle')}</span>
                          <ul className="text-xs text-slate-400 space-y-1">
                            {m.gap_analysis.map((gap, i) => (
                              <li key={i} className="flex items-center gap-1.5">
                                <span className="text-amber-400">⚠️</span> {gap}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: AI CITIZEN BLOGS */}
        {activeTab === 'blogs' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>📰</span> {t('hub.blogs.title')}
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  {t('hub.blogs.subtitle')}
                </p>
              </div>
              <Link
                to="/yojana/blogs"
                className="px-4 py-2 bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 text-xs font-semibold rounded-xl border border-indigo-500/30 transition-all self-start sm:self-auto"
              >
                {t('hub.blogs.viewAll', { count: blogs.length })}
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {blogs.length === 0 && (
                <p className="col-span-full py-8 text-center text-sm text-slate-400">{t('hub.blogs.empty')}</p>
              )}
              {blogs.map((b) => {
                const bannerImg = b.image_url || '/illustrations/pm_kisan_banner.jpg'
                return (
                  <div
                    key={b.id}
                    className="bg-slate-900/80 border border-slate-800 hover:border-indigo-500/50 rounded-2xl overflow-hidden transition-all shadow-xl hover:shadow-indigo-500/10 flex flex-col justify-between group"
                  >
                    <div>
                      {/* Photo Header */}
                      <div className="relative h-44 w-full overflow-hidden bg-slate-950">
                        <img
                          src={bannerImg}
                          alt={b.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/30 to-transparent" />
                        <div className="absolute top-3 left-3 right-3 flex items-center justify-between">
                          <span className="px-2.5 py-1 bg-slate-950/80 backdrop-blur-md text-indigo-300 border border-indigo-500/30 text-[10px] font-bold uppercase rounded-lg shadow-md">
                            {t('hub.blogs.badge')}
                          </span>
                          <span className="px-2.5 py-1 bg-slate-950/80 backdrop-blur-md text-slate-300 text-[10px] font-medium rounded-lg">
                            {new Date(b.published_at).toLocaleDateString(locale)}
                          </span>
                        </div>
                      </div>

                      <div className="p-5 space-y-3">
                        <h4 className="text-base font-extrabold text-white line-clamp-2 group-hover:text-indigo-300 transition-colors">
                          <Link to={`/yojana/blogs/${b.slug}`}>{b.title}</Link>
                        </h4>
                        <p className="text-xs text-slate-300 line-clamp-3 leading-relaxed">
                          {b.summary}
                        </p>
                      </div>
                    </div>

                    <div className="p-5 pt-0 space-y-4">
                      <div className="border-t border-slate-800/80 pt-3 flex flex-wrap items-center justify-between gap-2">
                        <div className="flex flex-wrap gap-1.5">
                          {b.official_links.map((link, i) => (
                            <a
                              key={i}
                              href={link.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[11px] text-emerald-400 hover:underline font-semibold bg-slate-950 border border-emerald-800/40 px-2 py-0.5 rounded-md"
                            >
                              {link.label} 🔗
                            </a>
                          ))}
                        </div>

                        <Link
                          to={`/yojana/blogs/${b.slug}`}
                          className="text-xs font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                        >
                          <span>{t('hub.blogs.read')}</span>
                          <span>→</span>
                        </Link>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}


      </div>
    </div>
  )
}

export default YojanaHub
