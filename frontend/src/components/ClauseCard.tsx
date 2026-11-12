import { useState } from 'react'
import type { Clause } from '../types'
import RiskBadge from './RiskBadge'
import { Card } from './Card'
import { UnclearTextPill } from './analysis/UnclearTextPill'

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

function renderTextWithUnclear(text: string) {
  if (!text || !text.includes('[UNCLEAR]')) {
    return text
  }
  const parts = text.split(/(\[UNCLEAR\])/g)
  return parts.map((part, index) => {
    if (part === '[UNCLEAR]') {
      return <UnclearTextPill key={index} />
    }
    return part
  })
}

export default function ClauseCard({ clause, index }: Props) {
  const [expanded, setExpanded] = useState(clause.risk_level === 'high')
  const [lang, setLang] = useState<'en' | 'hi' | 'src'>('en')
  const clauseNum = (clause as Clause & { clause_number?: string }).clause_number
  const pageNum = (clause as Clause & { page_number?: string | number }).page_number
  const tone = toneMap[clause.risk_level]

  const hasUnclear =
    Boolean(clause.is_unclear) ||
    Boolean(clause.original_text && clause.original_text.includes('[UNCLEAR]')) ||
    Boolean(clause.plain_english && clause.plain_english.includes('[UNCLEAR]'))

  // Show the "original language" option only for non-English documents that have it.
  const sourceLang = (clause.source_language || '').trim()
  const hasSource =
    Boolean(clause.plain_source && clause.plain_source.trim()) &&
    sourceLang.toLowerCase() !== 'english'
  // Very long documents are analysed in compact mode (no Hindi text) to fit free-tier AI limits.
  const hasHindi = Boolean(clause.plain_hindi && clause.plain_hindi.trim())
  const langOptions: [typeof lang, string][] = [
    ['en', 'English'],
    ...(hasHindi ? ([['hi', 'हिंदी']] as [typeof lang, string][]) : []),
    ...(hasSource ? ([['src', sourceLang || 'Original']] as [typeof lang, string][]) : []),
  ]
  const plainText =
    lang === 'hi'
      ? clause.plain_hindi
      : lang === 'src'
      ? clause.plain_source || clause.plain_english
      : clause.plain_english

  return (
    <Card variant="section" className={`overflow-hidden rounded-[26px] border-l-4 ${tone.line}`}>
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        aria-expanded={expanded}
        aria-label={`Clause ${index + 1}: ${clause.title}, Risk: ${clause.risk_level}. ${expanded ? 'Collapse' : 'Expand'}`}
        className="flex w-full items-start justify-between gap-4 px-5 py-5 text-left transition hover:bg-white/[0.02] sm:px-6 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-inset"
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
            {hasUnclear && (
              <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-[11px] text-amber-300 font-medium">
                ⚠️ Contains Unclear Text
              </span>
            )}
          </div>

          <h3 className="mt-4 text-lg font-semibold text-white sm:text-xl">{clause.title}</h3>
          <p className="mt-2 line-clamp-2 text-sm leading-7 text-slate-400">
            {renderTextWithUnclear(clause.plain_english)}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-3">
          <RiskBadge level={clause.risk_level} score={clause.risk_score} />
          <span className="mt-0.5 text-sm text-slate-500" aria-hidden="true">{expanded ? '▲' : '▼'}</span>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-white/8 px-5 pb-5 pt-5 sm:px-6 sm:pb-6 space-y-4">
          {hasUnclear && (
            <div className="rounded-[22px] border border-amber-500/30 bg-amber-500/10 p-4 space-y-1.5 text-xs text-amber-200">
              <div className="font-semibold text-amber-300 flex items-center gap-1.5">
                <span aria-hidden="true">⚠️</span>
                <span>Scan Uncertainty / Text Obscured</span>
              </div>
              <p className="leading-relaxed">
                Portions of this clause were unreadable in the uploaded document scan (due to a stamp, fold, or low resolution). This reflects scan clarity, not a legal flaw. Please verify against the original physical paper before acting.
              </p>
            </div>
          )}

          <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
            <div className="space-y-4">
              {clause.risk_reason && clause.risk_level !== 'low' && (
                <div className={`rounded-[22px] border px-4 py-4 ${tone.panel}`}>
                  <p className={`text-xs font-semibold uppercase tracking-[0.2em] ${tone.text}`}>{tone.label}</p>
                  <p className="mt-2 text-sm leading-7 text-slate-200">{clause.risk_reason}</p>
                </div>
              )}

              <Card variant="info" className="rounded-[22px] px-4 py-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Plain language</p>
                  <div className="flex items-center gap-0.5 rounded-full border border-white/10 bg-white/[0.03] p-0.5">
                    {langOptions.map(([key, label]) => (
                      <button
                        key={key}
                        type="button"
                        onClick={() => setLang(key)}
                        className={`rounded-full px-3 py-1 text-xs transition ${
                          lang === key ? 'bg-[#f5c26b]/15 text-[#f5c26b]' : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="text-sm leading-7 text-slate-300">{renderTextWithUnclear(plainText)}</div>
              </Card>
            </div>

            <details className="info-card h-fit rounded-[22px] px-4 py-4">
              <summary className="cursor-pointer text-sm font-medium text-white">View original legal text</summary>
              <div className="mt-4 whitespace-pre-wrap font-mono text-xs leading-7 text-slate-400">
                {renderTextWithUnclear(clause.original_text)}
              </div>
            </details>
          </div>
        </div>
      )}
    </Card>
  )
}
