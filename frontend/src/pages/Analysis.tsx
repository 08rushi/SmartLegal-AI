import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppSelector } from '../hooks/redux'
import ClauseCard from '../components/ClauseCard'
import RiskBadge from '../components/RiskBadge'
import type { RiskLevel } from '../types'

type FilterType = 'all' | RiskLevel

export default function Analysis() {
  const navigate = useNavigate()
  const { result, isLoading } = useAppSelector((s) => s.analysis)
  const currentDoc = useAppSelector((s) => s.document.current)
  const [filter, setFilter] = useState<FilterType>('all')
  const [showHindi, setShowHindi] = useState(false)

  useEffect(() => {
    if (!isLoading && !result) {
      navigate('/upload')
    }
  }, [result, isLoading, navigate])

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 gap-6">
        <div className="text-5xl animate-spin">⚖️</div>
        <div className="text-center">
          <p className="text-xl font-semibold text-gray-800">Analyzing your document...</p>
          <p className="text-gray-400 mt-1">Gemini AI is reading every clause</p>
        </div>
        <div className="flex gap-2">
          {['Extracting clauses', 'Scoring risks', 'Translating to Hindi'].map((s, i) => (
            <span
              key={s}
              className="text-xs bg-brand-100 text-brand-700 px-3 py-1.5 rounded-full animate-pulse"
              style={{ animationDelay: `${i * 0.4}s` }}
            >
              {s}
            </span>
          ))}
        </div>
      </div>
    )
  }

  if (!result) return null

  const { summary, clauses } = result

  const filteredClauses = filter === 'all'
    ? clauses
    : clauses.filter((c) => c.risk_level === filter)

  const riskColor = {
    high: 'text-red-600 bg-red-50 border-red-200',
    medium: 'text-amber-600 bg-amber-50 border-amber-200',
    low: 'text-green-600 bg-green-50 border-green-200',
  }

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-4xl mx-auto">

        {/* Document header */}
        <div className="flex items-start justify-between mb-6 flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                📄 {currentDoc?.filename || 'Document'}
              </span>
              <span className="text-xs text-gray-400">{summary.document_type}</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Analysis Result</h1>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/chat')}
              className="btn-primary text-sm"
            >
              💬 Ask questions about this doc
            </button>
            <button
              onClick={() => navigate('/upload')}
              className="btn-secondary text-sm"
            >
              Upload another
            </button>
          </div>
        </div>

        {/* Summary card */}
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
            <h2 className="text-lg font-semibold text-gray-900">Document Summary</h2>
            <RiskBadge level={summary.overall_risk} />
          </div>

          {/* Risk stats */}
          <div className="grid grid-cols-3 gap-4 mb-4">
            {[
              { label: 'High Risk', count: summary.high_risk_count, level: 'high' as RiskLevel },
              { label: 'Medium Risk', count: summary.medium_risk_count, level: 'medium' as RiskLevel },
              { label: 'Low Risk', count: summary.low_risk_count, level: 'low' as RiskLevel },
            ].map(({ label, count, level }) => (
              <button
                key={label}
                onClick={() => setFilter(filter === level ? 'all' : level)}
                className={`p-3 rounded-xl border text-center transition-all ${
                  filter === level
                    ? riskColor[level]
                    : 'bg-gray-50 border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
              >
                <div className="text-2xl font-bold">{count}</div>
                <div className="text-xs mt-0.5">{label}</div>
              </button>
            ))}
          </div>

          {/* Risk summary text */}
          <div className="bg-gray-50 rounded-xl p-4">
            <p className="text-sm font-medium text-gray-700 mb-1">
              🤖 AI Summary
            </p>
            <p className="text-sm text-gray-600">{summary.risk_summary}</p>
          </div>

          {/* Parties & dates */}
          {(summary.parties.length > 0 || summary.key_dates.length > 0) && (
            <div className="grid grid-cols-2 gap-4 mt-4">
              {summary.parties.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Parties</p>
                  {summary.parties.map((p) => (
                    <p key={p} className="text-sm text-gray-700">• {p}</p>
                  ))}
                </div>
              )}
              {summary.key_dates.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Key Dates</p>
                  {summary.key_dates.map((d) => (
                    <p key={d.label} className="text-sm text-gray-700">
                      <span className="text-gray-400">{d.label}:</span> {d.date}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Filter bar */}
        <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <h2 className="font-semibold text-gray-900">
              {filter === 'all' ? `All ${clauses.length} clauses` : `${filteredClauses.length} ${filter} risk clauses`}
            </h2>
            {filter !== 'all' && (
              <button
                onClick={() => setFilter('all')}
                className="text-xs text-brand-500 hover:underline"
              >
                clear filter
              </button>
            )}
          </div>
          <button
            onClick={() => setShowHindi(!showHindi)}
            className={`text-sm px-3 py-1.5 rounded-full border transition-colors ${
              showHindi
                ? 'bg-orange-50 border-orange-300 text-orange-700'
                : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
          >
            {showHindi ? '🇮🇳 हिंदी में देखें' : '🇮🇳 हिंदी में देखें'}
          </button>
        </div>

        {/* Clause list */}
        <div className="space-y-3">
          {filteredClauses.length === 0 ? (
            <div className="card text-center text-gray-400 py-10">
              No {filter} risk clauses found
            </div>
          ) : (
            filteredClauses.map((clause, i) => (
              <ClauseCard key={clause.id} clause={clause} index={i} />
            ))
          )}
        </div>
      </div>
    </div>
  )
}
