import { useState } from 'react'
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

export const documentArticles: DocumentArticle[] = [
  {
    id: 'rental-agreement',
    title: 'Rental Agreement',
    category: 'Housing',
    description: 'A complete guide to security deposits, lock-in clauses, notice periods, rent escalation, and landlord/tenant rights under Model Tenancy laws.',
    icon: '🏠',
    accent: 'from-[#2a3152] to-[#121a2d]',
    highlights: ['Deposit Caps', 'Notice Terms', 'Maintenance Duties'],
    fullContent: {
      overview:
        'A Rental Agreement is a legally binding contract executed between a property owner (landlord) and a tenant. Under Indian jurisprudence, a well-drafted rental agreement ensures clear boundaries for security deposits, maintenance obligations, eviction procedures, and notice periods.',
      legalFramework:
        'Regulated under state-specific Rent Control Acts, the Model Tenancy Act 2021 passed by the Union Cabinet, and Section 105 of the Transfer of Property Act 1882.',
      keyClauses: [
        {
          clauseName: 'Security Deposit Cap & Refund Timeline',
          purpose: 'Protects tenant funds and sets clear expectations for deduction rules upon move-out.',
          redFlags: 'Landlord reserving unlimited deduction rights or withholding refunds past 60 days without itemized receipts.',
          recommendedPhrasing: 'Security deposit shall not exceed 2 months rent for residential premises. The full deposit, less verified actual damages, must be refunded within 30 days of surrendering keys.',
        },
        {
          clauseName: 'Lock-in Period & Early Termination',
          purpose: 'Ensures both parties maintain stability for an initial agreed timeframe (e.g., 6 months).',
          redFlags: 'Harsh penalty clauses demanding payment for the entire remaining lease term if tenant relocates due to work.',
          recommendedPhrasing: 'Either party may terminate this agreement after the 6-month lock-in period by serving 1 month written notice or paying 1 month rent in lieu of notice.',
        },
      ],
      executionChecklist: [
        'Execute on Non-Judicial Stamp Paper of appropriate state denomination.',
        'If the tenancy duration exceeds 11 months, mandatory registration under Section 17 of the Indian Registration Act 1908 at the Sub-Registrar Office.',
        'Obtain mandatory Tenant Police Verification.',
        'Attach ID & Address proofs (Aadhaar/PAN) of both landlord and tenant alongside 2 independent witness signatures.',
      ],
      commonTraps: [
        'Oral promises regarding parking slots or pet permission not recorded in the written text.',
        'Not taking date-stamped move-in photos of existing wall cracks, appliances, or fixtures.',
      ],
      officialResources: [
        {
          title: 'Model Tenancy Act 2021 Policy & Provisions',
          url: 'https://mohua.gov.in',
          source: 'Ministry of Housing & Urban Affairs (MoHUA)',
          type: 'Official Portal',
        },
        {
          title: 'Transfer of Property Act 1882 (Section 105)',
          url: 'https://www.indiacode.nic.in',
          source: 'India Code',
          type: 'Government Gazette',
        },
      ],
    },
  },
  {
    id: 'employment-contract',
    title: 'Employment Contract',
    category: 'Employment',
    description: 'Understand non-compete limits, IP assignment, notice period buyouts, and severance rights under Indian labor codes.',
    icon: '💼',
    accent: 'from-[#1e293b] to-[#0f172a]',
    highlights: ['Notice Buyout', 'Non-Compete Limits', 'IP Ownership'],
    fullContent: {
      overview:
        'An Employment Contract defines the working relationship between employer and employee, governing compensation, duties, non-disclosure, intellectual property ownership, and termination conditions.',
      legalFramework:
        'Governed by the Code on Wages 2019, Section 27 of the Indian Contract Act 1872 (restraint of trade), Shops and Establishments Acts of respective states, and the Industrial Relations Code 2020.',
      keyClauses: [
        {
          clauseName: 'Non-Compete & Restraint of Trade (Section 27)',
          purpose: 'Restricts employee from joining a direct competitor during or after employment.',
          redFlags: 'Post-employment non-compete clauses restricting employment across India for 1–2 years.',
          recommendedPhrasing: 'Post-employment non-compete clauses are void under Section 27 of the Indian Contract Act 1872 unless restricted to non-solicitation of active clients or misuse of trade secrets.',
        },
      ],
      executionChecklist: [
        'Verify CTC breakup (Basic, HRA, PF, Gratuity, Special Allowance).',
        'Check probation evaluation criteria and notice period during probation.',
        'Ensure dual employment / moonlighting restrictions align with local state Shops & Establishment rules.',
      ],
      commonTraps: [
        'Undefined variable pay or discretionary performance bonus without clear metric targets.',
        'Excessive training bond penalties requiring multi-lakh repayments for early exit.',
      ],
      officialResources: [
        {
          title: 'Code on Wages 2019 Gazette Notification',
          url: 'https://labour.gov.in',
          source: 'Ministry of Labour & Employment',
          type: 'Government Gazette',
        },
      ],
    },
  },
]

export default function KnowledgeBase() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [activeModalArticle, setActiveModalArticle] = useState<DocumentArticle | null>(null)

  const categories = ['All', 'Housing', 'Employment', 'Finance', 'Business', 'Legal']

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
            Indian Citizen Legal Library
          </span>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight">
            Knowledge Base & Legal Guidance
          </h1>
          <p className="text-slate-400 max-w-2xl mx-auto text-base sm:text-lg">
            Plain-language explanations, clause breakdowns, statutory red flags, and verified Indian law checklists.
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
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
            <div className="bg-[#121a2d] border border-slate-700/80 rounded-3xl max-w-4xl w-full p-6 sm:p-8 space-y-6 relative max-h-[90vh] overflow-y-auto">
              <button
                onClick={() => setActiveModalArticle(null)}
                className="absolute top-6 right-6 text-slate-400 hover:text-white text-xl font-bold bg-slate-800/80 rounded-full w-10 h-10 flex items-center justify-center"
              >
                ✕
              </button>

              <div className="flex items-center gap-4">
                <span className="text-4xl p-3 bg-slate-800/80 rounded-2xl border border-slate-700/50">
                  {activeModalArticle.icon}
                </span>
                <div>
                  <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">
                    {activeModalArticle.category}
                  </span>
                  <h2 className="text-2xl sm:text-3xl font-bold text-white">
                    {activeModalArticle.title}
                  </h2>
                </div>
              </div>

              <div className="space-y-6 text-slate-300">
                <div className="bg-[#1a233a] p-5 rounded-2xl border border-slate-700/50">
                  <h4 className="text-white font-semibold text-sm uppercase tracking-wider mb-2">Overview</h4>
                  <p className="text-sm leading-relaxed">{activeModalArticle.fullContent.overview}</p>
                </div>

                <div className="bg-amber-400/5 p-5 rounded-2xl border border-amber-400/20">
                  <h4 className="text-amber-300 font-semibold text-sm uppercase tracking-wider mb-2">
                    Governing Indian Acts
                  </h4>
                  <p className="text-sm leading-relaxed text-amber-100">{activeModalArticle.fullContent.legalFramework}</p>
                </div>

                <div>
                  <h4 className="text-white font-bold text-lg mb-4">Critical Clauses & Red Flags</h4>
                  <div className="space-y-4">
                    {activeModalArticle.fullContent.keyClauses.map((clause, idx) => (
                      <div key={idx} className="bg-[#161f36] p-5 rounded-2xl border border-slate-800 space-y-2">
                        <h5 className="text-amber-400 font-semibold text-base">{clause.clauseName}</h5>
                        <p className="text-xs text-slate-300"><strong>Purpose:</strong> {clause.purpose}</p>
                        <p className="text-xs text-rose-300"><strong>⚠️ Red Flag:</strong> {clause.redFlags}</p>
                        <p className="text-xs text-emerald-300"><strong>✅ Recommended Term:</strong> {clause.recommendedPhrasing}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
