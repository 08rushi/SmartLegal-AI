const articles = [
  {
    title: 'Understanding Your Rental Agreement',
    description: 'A simple guide to deposits, lock-in periods, notice rules, and landlord obligations.',
    meta: '5 min read',
  },
  {
    title: 'Employment Contract: Key Things to Know',
    description: 'Important clauses you should never ignore in an employment contract.',
    meta: '7 min read',
  },
  {
    title: 'Loan Agreement Explained',
    description: 'Understand interest rates, penalties, and repayment terms before signing.',
    meta: '7 min read',
  },
]

export default function Compare() {
  return (
    <div className="content-wrap py-8 sm:py-10">
      <div className="section-card mx-auto max-w-7xl rounded-[32px] p-6 sm:p-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <span className="section-eyebrow">Knowledge Base</span>
            <h1 className="mt-4 text-3xl font-semibold text-white sm:text-4xl">Learn the legal terms that shape your rights.</h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400 sm:text-base">
              This page follows the reference board’s article-card direction and acts as a polished placeholder until side-by-side comparison tools are added.
            </p>
          </div>
          <button type="button" className="btn-secondary px-5 py-3">
            View All Articles
          </button>
        </div>

        <div className="mt-8 grid gap-4 lg:grid-cols-3">
          {articles.map((article, index) => (
            <article key={article.title} className="section-card hover-lift rounded-[28px] p-5">
              <div className="mb-5 flex h-40 items-end rounded-[24px] border border-white/10 bg-[radial-gradient(circle_at_top,rgba(124,58,237,0.24),transparent_55%),linear-gradient(180deg,#161b31,#0b1120)] p-4">
                <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs uppercase tracking-[0.2em] text-slate-400">
                  0{index + 1}
                </span>
              </div>
              <h2 className="text-2xl font-semibold text-white">{article.title}</h2>
              <p className="mt-3 text-sm leading-7 text-slate-400">{article.description}</p>
              <div className="mt-6 flex items-center justify-between text-sm">
                <span className="text-slate-500">{article.meta}</span>
                <button type="button" className="text-[#f5c26b] transition hover:text-white">
                  Read article →
                </button>
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  )
}
