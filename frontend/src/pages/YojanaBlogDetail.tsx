import React, { useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { fetchYojanaBlogBySlug } from '../store/yojanaSlice'

export const YojanaBlogDetail: React.FC = () => {
  const { slug } = useParams<{ slug: string }>()
  const dispatch = useAppDispatch()
  const { currentBlog, isLoading, error } = useAppSelector((s) => s.yojana)

  useEffect(() => {
    if (slug) {
      dispatch(fetchYojanaBlogBySlug(slug))
    }
  }, [dispatch, slug])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 py-16 text-center text-sm text-slate-400">
        Loading AI Citizen Guide...
      </div>
    )
  }

  if (error || !currentBlog) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 py-16 text-center space-y-4">
        <h2 className="text-xl font-bold text-slate-200">Citizen Guide Not Found</h2>
        <p className="text-xs text-slate-500">The requested scheme guide could not be located.</p>
        <Link to="/yojana" className="text-xs text-indigo-400 font-semibold underline">
          ← Return to Jan-Yojana Hub
        </Link>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Navigation Breadcrumb */}
        <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400">
          <Link to="/yojana" className="hover:underline">Jan-Yojana Hub</Link>
          <span>/</span>
          <Link to="/yojana/blogs" className="hover:underline">Citizen Guides</Link>
          <span>/</span>
          <span className="text-slate-500 truncate max-w-[200px]">{currentBlog.title}</span>
        </div>

        {/* Article Header Card */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl space-y-0">
          {/* Photo Banner */}
          <div className="relative h-64 sm:h-80 w-full overflow-hidden bg-slate-950">
            <img
              src={currentBlog.image_url || '/illustrations/pm_kisan_banner.jpg'}
              alt={currentBlog.title}
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/40 to-transparent" />
            <div className="absolute top-4 left-4 right-4 flex items-center justify-between">
              <span className="px-3 py-1 bg-slate-950/80 backdrop-blur-md text-indigo-300 border border-indigo-500/30 text-xs font-bold uppercase rounded-lg shadow-md">
                Verified Government Guide
              </span>
              <span className="px-3 py-1 bg-slate-950/80 backdrop-blur-md text-slate-300 text-xs font-medium rounded-lg">
                Published: {new Date(currentBlog.published_at).toLocaleDateString()}
              </span>
            </div>
          </div>

          <div className="p-6 sm:p-8 space-y-4">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white leading-tight">
              {currentBlog.title}
            </h1>

            <p className="text-sm text-slate-300 leading-relaxed border-l-2 border-indigo-500 pl-4 py-1 italic bg-indigo-950/20 rounded-r-xl">
              {currentBlog.summary}
            </p>

            {/* Official Link Bar */}
            <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center gap-3">
              <span className="text-xs font-semibold text-slate-400">Verified Official Portals:</span>
              {currentBlog.official_links.map((link, idx) => (
                <a
                  key={idx}
                  href={link.url}
                  target="_blank"
                  rel="noreferrer"
                  className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white text-xs font-bold rounded-xl shadow-lg transition-all flex items-center gap-2"
                >
                  <span>{link.label}</span>
                  <span className="text-xs">🔗</span>
                </a>
              ))}
            </div>
          </div>
        </div>

        {/* Simplified Citizen Visual Guidance Box */}
        <div className="bg-gradient-to-r from-amber-950/40 via-slate-900 to-slate-900 border border-amber-800/40 rounded-3xl p-6 sm:p-8 space-y-4 shadow-xl">
          <div className="flex items-center gap-2">
            <span className="text-xl">🇮🇳</span>
            <h3 className="text-base font-bold text-amber-300">आसान भाषा में समझें (Plain Language Guide for Citizens)</h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-slate-300 pt-2">
            <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-4 space-y-1">
              <span className="text-base">1️⃣</span>
              <h4 className="font-bold text-white">पात्रता जांचें (Eligibility)</h4>
              <p className="text-[11px] text-slate-400">आधार कार्ड, बैंक खाता और आय प्रमाण पत्र तैयार रखें।</p>
            </div>
            <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-4 space-y-1">
              <span className="text-base">2️⃣</span>
              <h4 className="font-bold text-white">ऑनलाइन आवेदन (Apply Online)</h4>
              <p className="text-[11px] text-slate-400">आधिकारिक वेबसाइट (.gov.in) पर जाकर आवेदन पत्र भरें।</p>
            </div>
            <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-4 space-y-1">
              <span className="text-base">3️⃣</span>
              <h4 className="font-bold text-white">सीधा बैंक ट्रांसफर (DBT Cash)</h4>
              <p className="text-[11px] text-slate-400">सत्यापन के बाद राशि आपके बैंक खाते में जमा होगी।</p>
            </div>
          </div>
        </div>

        {/* Article Markdown Body */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-3xl p-6 sm:p-10 space-y-6 text-slate-200 text-sm leading-relaxed whitespace-pre-line shadow-xl">
          {currentBlog.content_markdown}
        </div>


        {/* Footer Action Card */}
        <div className="bg-gradient-to-r from-indigo-900/40 via-slate-900 to-slate-900 border border-indigo-500/30 rounded-2xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-white">Check Your Eligibility For This Scheme</h3>
            <p className="text-xs text-slate-400 mt-0.5">Use our 30-second Rule Evaluation engine to check if you qualify.</p>
          </div>
          <Link
            to="/yojana"
            className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg transition-all flex-shrink-0"
          >
            ⚡ Test Eligibility Now
          </Link>
        </div>

      </div>
    </div>
  )
}

export default YojanaBlogDetail
