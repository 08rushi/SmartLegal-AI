import RiskBadge from '../RiskBadge'

interface AnalysisDashboardHeaderProps {
  filename: string
  docType: string
  analyzedAt: string
  overallRisk: 'low' | 'medium' | 'high'
  totalClauses: number
  highRiskCount: number
  mediumRiskCount: number
  lowRiskCount: number
  onExportPDF: () => void
}

export function AnalysisDashboardHeader({
  filename,
  docType,
  analyzedAt,
  overallRisk,
  totalClauses,
  highRiskCount,
  mediumRiskCount,
  lowRiskCount,
  onExportPDF,
}: AnalysisDashboardHeaderProps) {
  return (
    <div className="bg-[#121a2d]/90 border border-slate-800 rounded-3xl p-6 sm:p-8 backdrop-blur-xl space-y-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-xs font-bold text-amber-400 uppercase tracking-wider bg-amber-400/10 px-3 py-1 rounded-full border border-amber-400/20">
              {docType || 'Legal Document'}
            </span>
            <span className="text-xs text-slate-400">
              Analyzed: {analyzedAt ? new Date(analyzedAt).toLocaleDateString() : 'Just now'}
            </span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
            {filename}
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <RiskBadge level={overallRisk} />
          <button
            onClick={onExportPDF}
            className="px-5 py-2.5 bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold text-sm rounded-xl transition-all shadow-lg shadow-amber-400/20"
          >
            📥 Export PDF Report
          </button>
        </div>

      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-slate-800/80">
        <div className="bg-[#1a233a]/60 p-4 rounded-2xl border border-slate-800">
          <p className="text-xs text-slate-400 font-medium">Total Clauses</p>
          <p className="text-2xl font-extrabold text-white mt-1">{totalClauses}</p>
        </div>
        <div className="bg-rose-500/10 p-4 rounded-2xl border border-rose-500/20">
          <p className="text-xs text-rose-300 font-medium">High Risks</p>
          <p className="text-2xl font-extrabold text-rose-400 mt-1">{highRiskCount}</p>
        </div>
        <div className="bg-amber-500/10 p-4 rounded-2xl border border-amber-500/20">
          <p className="text-xs text-amber-300 font-medium">Medium Risks</p>
          <p className="text-2xl font-extrabold text-amber-400 mt-1">{mediumRiskCount}</p>
        </div>
        <div className="bg-emerald-500/10 p-4 rounded-2xl border border-emerald-500/20">
          <p className="text-xs text-emerald-300 font-medium">Low Risks</p>
          <p className="text-2xl font-extrabold text-emerald-400 mt-1">{lowRiskCount}</p>
        </div>
      </div>
    </div>
  )
}
