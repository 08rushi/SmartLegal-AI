import { useState } from 'react'
import { useTranslation } from 'react-i18next'

interface ClauseRewritePanelProps {
  originalClauseTitle: string
  originalText: string
}

export function ClauseRewritePanel({
  originalClauseTitle,
  originalText,
}: ClauseRewritePanelProps) {
  const { t } = useTranslation('analysis')
  const [rewrittenText, setRewrittenText] = useState('')
  const [loading, setLoading] = useState(false)

  const handleGenerateRewrite = () => {
    setLoading(true)
    setTimeout(() => {
      setRewrittenText(
        `${t('rewrite.heading', { title: originalClauseTitle || t('rewrite.fallbackTitle') })}\n\n` +
          `${t('rewrite.sample')}\n\n` +
          `${t('rewrite.reference', { text: originalText ? originalText.slice(0, 100) + '...' : t('rewrite.notAvailable') })}`
      )
      setLoading(false)
    }, 1000)
  }


  return (
    <div className="mt-3 bg-slate-950/80 border border-amber-400/20 p-4 rounded-2xl space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-amber-300 uppercase">
          💡 {t('rewrite.title')}
        </span>
        <button
          onClick={handleGenerateRewrite}
          disabled={loading}
          className="px-3 py-1.5 bg-amber-400/10 hover:bg-amber-400/20 border border-amber-400/30 text-amber-300 text-xs font-bold rounded-lg transition-all"
        >
          {loading ? t('rewrite.generating') : t('rewrite.generate')}
        </button>
      </div>

      {rewrittenText && (
        <div className="space-y-2 animate-fadeIn">
          <div className="bg-emerald-950/40 border border-emerald-500/30 p-3 rounded-xl text-xs text-emerald-200 font-mono whitespace-pre-wrap">
            {rewrittenText}
          </div>
          <p className="text-[11px] text-slate-400 italic">
            {t('rewrite.footnote')}
          </p>
        </div>
      )}
    </div>
  )
}
