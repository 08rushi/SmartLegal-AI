interface KnowledgeSearchBarProps {
  searchTerm: string
  setSearchTerm: (term: string) => void
  selectedCategory: string
  setSelectedCategory: (cat: string) => void
  categories: string[]
}

export function KnowledgeSearchBar({
  searchTerm,
  setSearchTerm,
  selectedCategory,
  setSelectedCategory,
  categories,
}: KnowledgeSearchBarProps) {
  return (
    <div className="mb-8 space-y-4">
      {/* Search Input */}
      <div className="relative">
        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-lg">🔍</span>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search legal guides, clauses, rent caps, notice rules..."
          className="w-full bg-[#121a2d]/80 border border-slate-700/80 rounded-xl pl-12 pr-4 py-3.5 text-white placeholder-slate-400 focus:outline-none focus:border-amber-400/80 transition-all shadow-inner"
        />
        {searchTerm && (
          <button
            onClick={() => setSearchTerm('')}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
          >
            ✕
          </button>
        )}
      </div>

      {/* Category Pills */}
      <div className="flex flex-wrap gap-2">
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              selectedCategory === category
                ? 'bg-amber-400 text-slate-900 font-semibold shadow-lg shadow-amber-400/20'
                : 'bg-[#1e293b]/70 text-slate-300 hover:bg-[#1e293b] border border-slate-700/50'
            }`}
          >
            {category}
          </button>
        ))}
      </div>
    </div>
  )
}
