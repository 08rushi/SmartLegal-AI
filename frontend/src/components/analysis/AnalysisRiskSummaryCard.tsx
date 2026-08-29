interface AnalysisRiskSummaryCardProps {
  riskSummary: string
  parties: string[]
  keyDates: { label: string; date: string }[]
  highRiskClauses: string[]
  yourObligations: string[]
}

export function AnalysisRiskSummaryCard({
  riskSummary,
  parties,
  keyDates,
  highRiskClauses,
  yourObligations,
}: AnalysisRiskSummaryCardProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Executive Summary */}
      <div className="lg:col-span-2 bg-[#121a2d]/80 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-4">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <span>📋</span> Executive Legal Summary
        </h3>
        <p className="text-slate-300 leading-relaxed text-base">
          {riskSummary || 'Analysis complete. Review the clauses below for key risk factors and legal obligations.'}
        </p>

        {highRiskClauses && highRiskClauses.length > 0 && (
          <div className="bg-rose-500/10 border border-rose-500/20 p-4 rounded-2xl space-y-2">
            <h4 className="text-rose-300 font-semibold text-sm">Most Critical Risk Points:</h4>
            <ul className="list-disc list-inside text-xs text-rose-200 space-y-1">
              {highRiskClauses.map((hr, idx) => (
                <li key={idx}>{hr}</li>
              ))}
            </ul>
          </div>
        )}

        {yourObligations && yourObligations.length > 0 && (
          <div className="bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-2xl space-y-2">
            <h4 className="text-emerald-300 font-semibold text-sm">Your Key Next Steps / Obligations:</h4>
            <ul className="list-disc list-inside text-xs text-emerald-200 space-y-1">
              {yourObligations.map((ob, idx) => (
                <li key={idx}>{ob}</li>
              ))}
            </ul>
          </div>
        )}
      </div>


      {/* Parties & Key Dates Sidebar */}
      <div className="bg-[#121a2d]/80 border border-slate-800 rounded-3xl p-6 space-y-6">
        {/* Parties */}
        <div>
          <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2">Parties Involved</h4>
          {parties && parties.length > 0 ? (
            <div className="space-y-1.5">
              {parties.map((p, idx) => (
                <div key={idx} className="bg-slate-800/60 text-slate-200 text-xs px-3 py-2 rounded-xl border border-slate-700/50 font-medium">
                  👥 {p}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400">No parties specified</p>
          )}
        </div>

        {/* Key Dates */}
        <div>
          <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2">Key Dates & Deadlines</h4>
          {keyDates && keyDates.length > 0 ? (
            <div className="space-y-1.5">
              {keyDates.map((kd, idx) => (
                <div key={idx} className="flex items-center justify-between bg-slate-800/60 text-xs p-2.5 rounded-xl border border-slate-700/50">
                  <span className="text-slate-300">{kd.label}</span>
                  <span className="text-amber-300 font-semibold">{kd.date}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400">No key dates detected</p>
          )}
        </div>
      </div>
    </div>
  )
}
