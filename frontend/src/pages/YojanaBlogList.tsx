import React, { useEffect } from 'react'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { fetchYojanaBlogs } from '../store/yojanaSlice'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export const YojanaBlogList: React.FC = () => {
  const { t, i18n } = useTranslation('yojana')
  const lang = i18n.language.slice(0, 2)
  const locale = `${lang}-IN`
  const dispatch = useAppDispatch()
  const { blogs, isLoading } = useAppSelector((s) => s.yojana)

  useEffect(() => {
    // TODO(i18n-content): blog title/summary/body arrive in the active language once the backend
    // supports `lang` (X-Lang header is already sent; refetch when the language changes).
    dispatch(fetchYojanaBlogs())
  }, [dispatch, lang])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="border-b border-slate-800 pb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400 mb-1">
              <Link to="/yojana" className="hover:underline">{t('blogList.breadcrumbHub')}</Link>
              <span>/</span>
              <span>{t('blogList.breadcrumbGuides')}</span>
            </div>
            <h1 className="text-3xl font-extrabold text-white">{t('blogList.title')}</h1>
            <p className="text-sm text-slate-400 mt-1">
              {t('blogList.subtitle')}
            </p>
          </div>

          <Link
            to="/yojana"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg transition-all self-start sm:self-auto"
          >
            {t('blogList.ctaTest')}
          </Link>
        </div>

        {/* Grid of Blog Posts */}
        {isLoading ? (
          <div className="py-12 text-center text-slate-500 text-sm">
            {t('blogList.loading')}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {blogs.length === 0 && (
              <p className="col-span-full py-8 text-center text-sm text-slate-400">{t('blogList.empty')}</p>
            )}
            {blogs.map((b) => {
              const bannerImg = b.image_url || '/illustrations/pm_kisan_banner.jpg'
              return (
                <article
                  key={b.id}
                  className="bg-slate-900/80 border border-slate-800 hover:border-indigo-500/50 rounded-2xl overflow-hidden transition-all shadow-xl hover:shadow-indigo-500/10 flex flex-col justify-between group"
                >
                  <div>
                    {/* Header Photo Banner */}
                    <div className="relative h-48 w-full overflow-hidden bg-slate-950">
                      <img
                        src={bannerImg}
                        alt={b.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/30 to-transparent" />
                      <div className="absolute top-3 left-3 right-3 flex items-center justify-between">
                        <span className="px-2.5 py-1 bg-slate-950/80 backdrop-blur-md text-indigo-300 border border-indigo-500/30 text-[10px] font-bold uppercase rounded-lg shadow-md">
                          {t('blogList.badge')}
                        </span>
                        <span className="px-2.5 py-1 bg-slate-900/80 backdrop-blur-md text-slate-300 text-[10px] font-medium rounded-lg">
                          {new Date(b.published_at).toLocaleDateString(locale)}
                        </span>
                      </div>
                    </div>

                    <div className="p-5 space-y-3">
                      <h2 className="text-base font-extrabold text-white line-clamp-2 group-hover:text-indigo-300 transition-colors">
                        <Link to={`/yojana/blogs/${b.slug}`}>{b.title}</Link>
                      </h2>

                      <p className="text-xs text-slate-300 line-clamp-3 leading-relaxed">
                        {b.summary}
                      </p>
                    </div>
                  </div>

                  <div className="p-5 pt-0 space-y-4">
                    <div className="border-t border-slate-800/80 pt-3 space-y-3">
                      <div className="flex flex-wrap gap-2">
                        {b.official_links.map((link, i) => (
                          <a
                            key={i}
                            href={link.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[11px] bg-slate-950 text-emerald-400 border border-emerald-800/50 hover:bg-emerald-950/30 px-2.5 py-1 rounded-lg font-semibold transition-all flex items-center gap-1"
                          >
                            {link.label} 🔗
                          </a>
                        ))}
                      </div>

                      <Link
                        to={`/yojana/blogs/${b.slug}`}
                        className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-400 hover:text-indigo-300 pt-1"
                      >
                        <span>{t('blogList.read')}</span>
                        <span>→</span>
                      </Link>
                    </div>
                  </div>
                </article>
              )
            })}
          </div>
        )}


      </div>
    </div>
  )
}

export default YojanaBlogList
