import { useState } from 'react'

interface ClauseRewritePanelProps {
  originalClauseTitle: string
  originalText: string
}

export function ClauseRewritePanel({
  originalClauseTitle,
  originalText,
}: ClauseRewritePanelProps) {
  const [rewrittenText, setRewrittenText] = useState('')
  const [loading, setLoading] = useState(false)

  const handleGenerateRewrite = () => {
    setLoading(true)
    setTimeout(() => {
      setRewrittenText(
        `Suggested Fair Wording for "${originalClauseTitle || 'Clause'}":\n\n` +
          `"Either party may terminate this agreement by giving 30 days prior written notice. ` +
          `The security deposit shall be refunded in full within 7 working days of vacating the premises, ` +
          `subject only to normal wear and tear and agreed utility deductions."\n\n` +
          `Original Text Reference: ${originalText ? originalText.slice(0, 100) + '...' : 'N/A'}`
      )
      setLoading(false)
    }, 1000)
  }


  return (
    <div className="mt-3 bg-slate-950/80 border border-amber-400/20 p-4 rounded-2xl space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-amber-300 uppercase">
          💡 AI Negotiation Wording Generator (SL-067)
        </span>
        <button
          onClick={handleGenerateRewrite}
          disabled={loading}
          className="px-3 py-1.5 bg-amber-400/10 hover:bg-amber-400/20 border border-amber-400/30 text-amber-300 text-xs font-bold rounded-lg transition-all"
        >
          {loading ? 'Generating...' : 'Generate Balanced Counter-Wording'}
        </button>
      </div>

      {rewrittenText && (
        <div className="space-y-2 animate-fadeIn">
          <div className="bg-emerald-950/40 border border-emerald-500/30 p-3 rounded-xl text-xs text-emerald-200 font-mono whitespace-pre-wrap">
            {rewrittenText}
          </div>
          <p className="text-[11px] text-slate-400 italic">
            * Use this suggested wording in discussions with the landlord, employer, or lender before signing.
          </p>
        </div>
      )}
    </div>
  )
}
