import { useState } from 'react'
import type { Clause } from '../types'
import RiskBadge from './RiskBadge'

interface Props {
  clause: Clause
  index: number
}

const borderColor = {
  high: 'border-l-red-500',
  medium: 'border-l-amber-500',
  low: 'border-l-green-500',
}

const bgColor = {
  high: 'bg-red-50',
  medium: 'bg-amber-50',
  low: 'bg-green-50',
}

export default function ClauseCard({ clause, index }: Props) {
  const [expanded, setExpanded] = useState(clause.risk_level === 'high')
  const [showHindi, setShowHindi] = useState(false)

  return (
    <div
      className={`bg-white border border-gray-200 border-l-4 ${borderColor[clause.risk_level]} rounded-xl overflow-hidden shadow-sm transition-all duration-200`}
    >
      {/* Header - always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left p-5 flex items-start justify-between gap-4 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-start gap-3 min-w-0">
          <span className="text-xs font-mono text-gray-400 bg-gray-100 px-2 py-1 rounded mt-0.5 shrink-0">
            #{index + 1}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="font-semibold text-gray-900">{clause.title}</h3>
              <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                {clause.clause_type}
              </span>
            </div>
            <p className="text-sm text-gray-500 mt-1 line-clamp-2">{clause.plain_english}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <RiskBadge level={clause.risk_level} score={clause.risk_score} />
          <span className="text-gray-400 text-sm">{expanded ? '▲' : '▼'}</span>
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="px-5 pb-5 space-y-4 border-t border-gray-100">

          {/* Risk warning */}
          {clause.risk_level !== 'low' && clause.risk_reason && (
            <div className={`${bgColor[clause.risk_level]} rounded-lg p-3 mt-4`}>
              <p className="text-sm font-medium text-gray-700 mb-1">
                {clause.risk_level === 'high' ? '🚨' : '⚠️'} Why this is risky
              </p>
              <p className="text-sm text-gray-600">{clause.risk_reason}</p>
            </div>
          )}

          {/* Plain language toggle */}
          <div className="mt-4">
            <div className="flex items-center gap-2 mb-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Plain language
              </p>
              <button
                onClick={() => setShowHindi(!showHindi)}
                className={`text-xs px-2 py-0.5 rounded-full border transition-colors ${
                  showHindi
                    ? 'bg-orange-50 border-orange-300 text-orange-700'
                    : 'bg-gray-100 border-gray-200 text-gray-600 hover:bg-orange-50'
                }`}
              >
                {showHindi ? '🇮🇳 Hindi' : '🇬🇧 English'} — click to switch
              </button>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed">
              {showHindi ? clause.plain_hindi : clause.plain_english}
            </p>
          </div>

          {/* Original text */}
          <details className="mt-2">
            <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600">
              View original legal text
            </summary>
            <p className="text-xs text-gray-500 mt-2 font-mono leading-relaxed bg-gray-50 p-3 rounded-lg border border-gray-200">
              {clause.original_text}
            </p>
          </details>
        </div>
      )}
    </div>
  )
}
