import { useState } from 'react'
import type { Clause } from '../types'
import RiskBadge from './RiskBadge'

interface Props {
  clause: Clause
  index: number
}

const toneMap = {
  high: {
    line: 'border-l-[#fb7185]',
    panel: 'bg-[#2a1320]/65 border-[#fb7185]/20',
    text: 'text-[#fecdd3]',
    label: 'Risk warning',
  },
  medium: {
    line: 'border-l-[#f5c26b]',
    panel: 'bg-[#2a2410]/60 border-[#f5c26b]/20',
    text: 'text-[#fde68a]',
    label: 'Watch closely',
  },
  low: {
    line: 'border-l-[#34d399]',
    panel: 'bg-[#10241f]/60 border-[#34d399]/20',
    text: 'text-[#bbf7d0]',
    label: 'Low risk',
  },
}

export default function ClauseCard({ clause, index }: Props) {
  const [expanded, setExpanded] = useState(clause.risk_level === 'high')
  const [showHindi, setShowHindi] = useState(false)
  const clauseNum = (clause as Clause & { clause_number?: string }).clause_number
  const pageNum = (clause as Clause & { page_number?: string | number }).page_number
  const tone = toneMap[clause.risk_level]

  return (
    <div className={`section-card overflow-hidden rounded-[26px] border-l-4 ${tone.line}`}>
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="flex w-full items-start justify-between gap-4 px-5 py-5 text-left transition hover:bg-white/[0.02] sm:px-6"
      >
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[11px] uppercase tracking-[0.2em] text-slate-500">
              {String(index + 1).padStart(2, '0')}
            </span>
            <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[11px] text-slate-400">
              {clause.clause_type}
            </span>
            {clauseNum && clauseNum !== 'Unnumbered clause' && (
              <span className="rounded-full border border-[#8a5cff]/25 bg-[#8a5cff]/10 px-2.5 py-1 text-[11px] text-[#c5b4ff]">
                {clauseNum}
              </span>
            )}
            {pageNum && (
              <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[11px] text-slate-400">
                Page {pageNum}
              </span>
            )}
          </div>

          <h3 className="mt-4 text-lg font-semibold text-white sm:text-xl">{clause.title}</h3>
          <p className="mt-2 line-clamp-2 text-sm leading-7 text-slate-400">{clause.plain_english}</p>
        </div>

        <div className="flex shrink-0 items-center gap-3">
          <RiskBadge level={clause.risk_level} score={clause.risk_score} />
          <span className="mt-0.5 text-sm text-slate-500">{expanded ? '▲' : '▼'}</span>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-white/8 px-5 pb-5 pt-5 sm:px-6 sm:pb-6">
          <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
            <div className="space-y-4">
              {clause.risk_reason && clause.risk_level !== 'low' && (
                <div className={`rounded-[22px] border px-4 py-4 ${tone.panel}`}>
                  <p className={`text-xs font-semibold uppercase tracking-[0.2em] ${tone.text}`}>{tone.label}</p>
                  <p className="mt-2 text-sm leading-7 text-slate-200">{clause.risk_reason}</p>
                </div>
              )}

              <div className="info-card rounded-[22px] px-4 py-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Plain language</p>
                  <button
                    type="button"
                    onClick={() => setShowHindi((value) => !value)}
                    className={`rounded-full border px-3 py-1 text-xs transition ${
                      showHindi
                        ? 'border-[#f5c26b]/25 bg-[#f5c26b]/10 text-[#f5c26b]'
                        : 'border-white/10 bg-white/[0.03] text-slate-400 hover:text-white'
                    }`}
                  >
                    {showHindi ? 'Hindi' : 'English'}
                  </button>
                </div>
                <p className="text-sm leading-7 text-slate-300">
                  {showHindi ? clause.plain_hindi : clause.plain_english}
                </p>
              </div>
            </div>

            <details className="info-card h-fit rounded-[22px] px-4 py-4">
              <summary className="cursor-pointer text-sm font-medium text-white">View original legal text</summary>
              <p className="mt-4 whitespace-pre-wrap font-mono text-xs leading-7 text-slate-400">
                {clause.original_text}
              </p>
            </details>
          </div>
        </div>
      )}
    </div>
  )
}
