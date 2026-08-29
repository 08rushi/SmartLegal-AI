import { DocumentArticle } from '../../pages/KnowledgeBase'

interface KnowledgeArticleCardProps {
  article: DocumentArticle
  onSelect: (article: DocumentArticle) => void
}

export function KnowledgeArticleCard({ article, onSelect }: KnowledgeArticleCardProps) {
  return (
    <div
      onClick={() => onSelect(article)}
      className="group relative bg-[#121a2d]/80 border border-slate-800/80 hover:border-amber-400/50 rounded-2xl p-6 transition-all duration-300 hover:shadow-2xl hover:shadow-amber-400/10 cursor-pointer flex flex-col justify-between overflow-hidden backdrop-blur-xl"
    >
      <div className="space-y-4">
        {/* Category Header */}
        <div className="flex items-center justify-between">
          <span className="text-3xl p-2.5 bg-slate-800/60 rounded-xl border border-slate-700/50 group-hover:scale-110 transition-transform">
            {article.icon}
          </span>
          <span className="px-3 py-1 bg-amber-400/10 text-amber-300 text-xs font-semibold rounded-full border border-amber-400/20">
            {article.category}
          </span>
        </div>

        {/* Title & Description */}
        <div>
          <h3 className="text-xl font-bold text-white group-hover:text-amber-300 transition-colors mb-2">
            {article.title}
          </h3>
          <p className="text-slate-400 text-sm line-clamp-3 leading-relaxed">
            {article.description}
          </p>
        </div>

        {/* Highlights */}
        <div className="flex flex-wrap gap-1.5 pt-2">
          {article.highlights.map((h, idx) => (
            <span key={idx} className="px-2.5 py-0.5 bg-slate-800/80 text-slate-300 text-xs rounded-md">
              ✓ {h}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-amber-400 font-medium text-sm group-hover:translate-x-1 transition-transform">
        <span>Read Complete Breakdown</span>
        <span>→</span>
      </div>
    </div>
  )
}
