import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import { Modal } from '../components/ui/Modal'
import { KnowledgeSearchBar } from '../components/knowledge/KnowledgeSearchBar'
import { KnowledgeArticleCard } from '../components/knowledge/KnowledgeArticleCard'

export interface ArticleResource {
  title: string
  url: string
  source: string
  type: 'Official Portal' | 'Government Gazette' | 'Verified Legal Resource'
}

export interface ArticleClauseBreakdown {
  clauseName: string
  purpose: string
  redFlags: string
  recommendedPhrasing: string
}

export interface DocumentArticle {
  id: string
  title: string
  category: 'Housing' | 'Employment' | 'Finance' | 'Business' | 'Legal'
  description: string
  icon: string
  accent: string
  highlights: string[]
  fullContent: {
    overview: string
    legalFramework: string
    keyClauses: ArticleClauseBreakdown[]
    executionChecklist: string[]
    commonTraps: string[]
    officialResources: ArticleResource[]
  }
}

export type ArticleCategory = DocumentArticle['category']

// Language-independent article metadata. All text lives in locales/<lang>/knowledge.json under
// `articles.<id>`. Add a new article by adding an entry here AND its text in en/hi/mr.
interface ArticleMeta {
  id: string
  category: ArticleCategory
  icon: string
  accent: string
  resources: { url: string; type: ArticleResource['type'] }[]
}

const ARTICLE_META: ArticleMeta[] = [
  {
    id: 'rental-agreement',
    category: 'Housing',
    icon: '🏠',
    accent: 'from-[#2a3152] to-[#121a2d]',
    resources: [
      { url: 'https://mohua.gov.in', type: 'Official Portal' },
      { url: 'https://www.indiacode.nic.in', type: 'Government Gazette' },
    ],
  },
  {
    id: 'employment-contract',
    category: 'Employment',
    icon: '💼',
    accent: 'from-[#1e293b] to-[#0f172a]',
    resources: [{ url: 'https://labour.gov.in', type: 'Government Gazette' }],
  },
]

const CATEGORIES: ('All' | ArticleCategory)[] = ['All', 'Housing', 'Employment', 'Finance', 'Business', 'Legal']

/** Builds the articles with text in the active language. */
export function localizeArticles(t: TFunction): DocumentArticle[] {
  const list = (key: string) => t(key, { returnObjects: true }) as unknown as string[]
  return ARTICLE_META.map((m) => {
    const k = `articles.${m.id}`
    const clauses = t(`${k}.keyClauses`, { returnObjects: true }) as unknown as ArticleClauseBreakdown[]
    const res = t(`${k}.resources`, { returnObjects: true }) as unknown as { title: string; source: string }[]
    return {
      id: m.id,
      title: t(`${k}.title`),
      category: m.category,
      description: t(`${k}.description`),
      icon: m.icon,
      accent: m.accent,
      highlights: list(`${k}.highlights`),
      fullContent: {
        overview: t(`${k}.overview`),
        legalFramework: t(`${k}.legalFramework`),
        keyClauses: Array.isArray(clauses) ? clauses : [],
        executionChecklist: list(`${k}.executionChecklist`),
        commonTraps: list(`${k}.commonTraps`),
        officialResources: m.resources.map((r, idx) => ({
          url: r.url,
          type: r.type,
          title: res?.[idx]?.title ?? r.url,
          source: res?.[idx]?.source ?? '',
        })),
      },
    }
  })
}

export default function KnowledgeBase() {
  const { t } = useTranslation('knowledge')
  const documentArticles = useMemo(() => localizeArticles(t), [t])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [activeModalArticle, setActiveModalArticle] = useState<DocumentArticle | null>(null)

  const categories = CATEGORIES

  const filteredArticles = documentArticles.filter((article) => {
    const matchesSearch =
      article.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      article.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === 'All' || article.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-10">
        {/* Header */}
        <div className="text-center space-y-4">
          <span className="px-4 py-1.5 bg-amber-400/10 text-amber-300 rounded-full text-xs font-semibold uppercase tracking-wider border border-amber-400/20">
            {t('badge')}
          </span>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">
            {t('title')}
          </h1>
          <p className="text-slate-400 max-w-2xl mx-auto text-base sm:text-lg">
            {t('subtitle')}
          </p>
        </div>

        {/* Search & Filters */}
        <KnowledgeSearchBar
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          selectedCategory={selectedCategory}
          setSelectedCategory={setSelectedCategory}
          categories={categories}
        />

        {/* Articles Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredArticles.map((article) => (
            <KnowledgeArticleCard
              key={article.id}
              article={article}
              onSelect={(art) => setActiveModalArticle(art)}
            />
          ))}
        </div>

        {/* Modal for Article Detail */}
        {activeModalArticle && (
          <Modal
            isOpen
            onClose={() => setActiveModalArticle(null)}
            look="card"
            size="xl"
            ariaLabel={activeModalArticle.title}
          >
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <span className="text-4xl p-3 bg-slate-800/80 rounded-2xl border border-slate-700/50">
                  {activeModalArticle.icon}
                </span>
                <div>
                  <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">
                    {t(`categories.${activeModalArticle.category}`)}
                  </span>
                  <h2 className="text-2xl sm:text-3xl font-bold text-white">
                    {activeModalArticle.title}
                  </h2>
                </div>
              </div>

              <div className="space-y-6 text-slate-300">
                <div className="bg-[#1a233a] p-5 rounded-2xl border border-slate-700/50">
                  <h4 className="text-white font-semibold text-sm uppercase tracking-wider mb-2">{t('modal.overview')}</h4>
                  <p className="text-sm leading-relaxed">{activeModalArticle.fullContent.overview}</p>
                </div>

                <div className="bg-amber-400/5 p-5 rounded-2xl border border-amber-400/20">
                  <h4 className="text-amber-300 font-semibold text-sm uppercase tracking-wider mb-2">
                    {t('modal.acts')}
                  </h4>
                  <p className="text-sm leading-relaxed text-amber-100">{activeModalArticle.fullContent.legalFramework}</p>
                </div>

                <div>
                  <h4 className="text-white font-bold text-lg mb-4">{t('modal.clauses')}</h4>
                  <div className="space-y-4">
                    {activeModalArticle.fullContent.keyClauses.map((clause, idx) => (
                      <div key={idx} className="bg-[#161f36] p-5 rounded-2xl border border-slate-800 space-y-2">
                        <h5 className="text-amber-400 font-semibold text-base">{clause.clauseName}</h5>
                        <p className="text-xs text-slate-300"><strong>{t('modal.purpose')}</strong> {clause.purpose}</p>
                        <p className="text-xs text-rose-300"><strong>⚠️ {t('modal.redFlag')}</strong> {clause.redFlags}</p>
                        <p className="text-xs text-emerald-300"><strong>✅ {t('modal.recommended')}</strong> {clause.recommendedPhrasing}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <p className="text-xs text-slate-400">{t('modal.disclaimer')}</p>
              </div>
            </div>
          </Modal>
        )}
      </div>
    </div>
  )
}
