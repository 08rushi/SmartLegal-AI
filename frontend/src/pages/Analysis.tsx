import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ClauseCard from '../components/ClauseCard'
import RiskBadge from '../components/RiskBadge'
import { useAppSelector } from '../hooks/redux'
import type { RiskLevel } from '../types'

type FilterType = 'all' | RiskLevel

const sidebarItems = ['Overview', 'Key Points', 'All Clauses', 'Risk Warnings', 'Ask AI']

export default function Analysis() {
  const navigate = useNavigate()
  const { result, isLoading, error } = useAppSelector((s) => s.analysis)
  const currentDoc = useAppSelector((s) => s.document.current)
  const [filter, setFilter] = useState<FilterType>('all')
  const [activeTab, setActiveTab] = useState<'clauses' | 'summary'>('summary')

  useEffect(() => {
    if (!isLoading && !result) {
      navigate('/upload')
    }
  }, [result, isLoading, navigate])

  if (isLoading) {
    return (
      <div className="content-wrap py-10">
        <div className="section-card mx-auto flex max-w-4xl flex-col items-center gap-6 rounded-[32px] px-6 py-16 text-center">
          <div className="flex h-24 w-24 items-center justify-center rounded-[30px] border border-[#8a5cff]/25 bg-[#8a5cff]/10 text-4xl text-[#c5b4ff] shadow-[0_0_40px_rgba(124,58,237,0.24)]">
            ⚖
          </div>
          <div>
            <h1 className="text-3xl font-semibold text-white">Analyzing your document...</h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-400 sm:text-base">
              AI is reading every clause and building a structured overview. Larger contracts can take a minute or two.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-2">
            {['Splitting sections', 'Extracting clauses', 'Scoring risk', 'Building summary'].map((item) => (
              <span key={item} className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-300">
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="content-wrap py-10">
        <div className="section-card mx-auto max-w-3xl rounded-[32px] px-6 py-14 text-center">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-[28px] border border-[#fb7185]/20 bg-[#fb7185]/10 text-3xl text-[#fecdd3]">
            !
          </div>
          <h1 className="mt-6 text-3xl font-semibold text-white">Analysis Failed</h1>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-slate-400">{error}</p>
          <button onClick={() => navigate('/upload')} className="btn-primary mt-8">
            Try Again
          </button>
        </div>
      </div>
    )
  }

  if (!result) return null

  const { summary, clauses } = result
  const filteredClauses = filter === 'all' ? clauses : clauses.filter((c) => c.risk_level === filter)
  const highRiskClauses: string[] = (summary as typeof summary & { high_risk_clauses?: string[] }).high_risk_clauses || []
  const beneficialClauses: string[] = (summary as typeof summary & { beneficial_clauses?: string[] }).beneficial_clauses || []
  const yourObligations: string[] =
    (summary as typeof summary & { your_obligations?: string[]; tenant_obligations?: string[] }).your_obligations ||
    (summary as typeof summary & { tenant_obligations?: string[] }).tenant_obligations ||
    []
  const otherPartyRights: string[] =
    (summary as typeof summary & { other_party_rights?: string[]; landlord_rights?: string[] }).other_party_rights ||
    (summary as typeof summary & { landlord_rights?: string[] }).landlord_rights ||
    []

  return (
    <div className="content-wrap py-8 sm:py-10">
      <div className="mx-auto grid max-w-7xl gap-6 xl:grid-cols-[260px_minmax(0,1fr)]">
        <aside className="section-card h-fit rounded-[30px] p-5">
          <div className="mb-6">
            <p className="text-sm text-slate-500">Analysis Overview</p>
            <h1 className="mt-2 text-2xl font-semibold text-white">Document Review</h1>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              {currentDoc?.filename || 'Uploaded document'}
            </p>
          </div>

          <div className="space-y-2">
            {sidebarItems.map((item, index) => (
              <button
                key={item}
                type="button"
                onClick={() => {
                  if (item === 'All Clauses') setActiveTab('clauses')
                  if (item === 'Ask AI') navigate('/chat')
                  if (item === 'Overview' || item === 'Key Points' || item === 'Risk Warnings') setActiveTab('summary')
                }}
                className={`flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm transition ${
                  (activeTab === 'summary' && index < 2) || (activeTab === 'clauses' && item === 'All Clauses')
                    ? 'bg-white/10 text-[#f5c26b]'
                    : 'text-slate-400 hover:bg-white/[0.03] hover:text-white'
                }`}
              >
                <span className="text-xs text-slate-500">{String(index + 1).padStart(2, '0')}</span>
                <span>{item}</span>
              </button>
            ))}
          </div>
        </aside>

        <div className="space-y-6">
          <section className="section-card rounded-[30px] p-5 sm:p-7">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <p className="text-sm text-slate-500">Document: {currentDoc?.filename || 'Legal Agreement.pdf'}</p>
                <h2 className="mt-2 text-3xl font-semibold text-white">Analysis Overview</h2>
                <p className="mt-2 text-sm leading-7 text-slate-400">
                  Review risk counts, core obligations, and your contract summary in one structured dashboard.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <button onClick={() => navigate('/chat')} className="btn-primary">
                  Ask About This Document
                </button>
                <button onClick={() => navigate('/upload')} className="btn-secondary">
                  Upload Another
                </button>
              </div>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <div className="metric-card rounded-[22px] p-4">
                <p className="text-4xl font-semibold text-white">{summary.total_clauses}</p>
                <p className="mt-1 text-sm text-slate-400">Total clauses</p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setFilter('high')
                  setActiveTab('clauses')
                }}
                className="metric-card rounded-[22px] p-4 text-left transition hover:border-[#fb7185]/25"
              >
                <p className="text-4xl font-semibold text-[#fb7185]">{summary.high_risk_count}</p>
                <p className="mt-1 text-sm text-slate-400">High risk items</p>
              </button>
              <button
                type="button"
                onClick={() => {
                  setFilter('medium')
                  setActiveTab('clauses')
                }}
                className="metric-card rounded-[22px] p-4 text-left transition hover:border-[#f5c26b]/25"
              >
                <p className="text-4xl font-semibold text-[#f5c26b]">{summary.medium_risk_count}</p>
                <p className="mt-1 text-sm text-slate-400">Medium risk items</p>
              </button>
              <div className="metric-card rounded-[22px] p-4">
                <RiskBadge level={summary.overall_risk} />
                <p className="mt-4 text-sm leading-7 text-slate-400">Overall contract risk profile</p>
              </div>
            </div>

            <div className="mt-6 grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
              <div className="info-card rounded-[24px] p-5">
                <p className="text-sm font-medium text-white">AI Summary</p>
                <p className="mt-3 text-sm leading-7 text-slate-300">{summary.risk_summary}</p>
              </div>

              <div className="info-card rounded-[24px] p-5">
                <p className="text-sm font-medium text-white">Document Details</p>
                <div className="mt-4 space-y-3 text-sm text-slate-300">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-slate-500">Type</span>
                    <span>{summary.document_type}</span>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-slate-500">Parties</span>
                    <span>{summary.parties.length || 0}</span>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-slate-500">Key dates</span>
                    <span>{summary.key_dates.length || 0}</span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {activeTab === 'summary' && (
            <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
              <div className="section-card rounded-[30px] p-5 sm:p-6">
                <div className="mb-5 flex items-center justify-between gap-4">
                  <h3 className="text-2xl font-semibold text-white">Key Points</h3>
                  <button type="button" onClick={() => setActiveTab('clauses')} className="btn-secondary px-4 py-2.5 text-sm">
                    View All Clauses
                  </button>
                </div>

                <div className="space-y-4">
                  {highRiskClauses.length > 0 && (
                    <div className="rounded-[24px] border border-[#fb7185]/18 bg-[#2a1320]/55 p-5">
                      <p className="text-sm font-medium text-[#fecdd3]">High Risk Clauses</p>
                      <ul className="mt-3 space-y-2 text-sm leading-7 text-slate-200">
                        {highRiskClauses.map((item) => (
                          <li key={item}>• {item}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {beneficialClauses.length > 0 && (
                    <div className="rounded-[24px] border border-[#34d399]/18 bg-[#10241f]/55 p-5">
                      <p className="text-sm font-medium text-[#bbf7d0]">Clauses That Protect You</p>
                      <ul className="mt-3 space-y-2 text-sm leading-7 text-slate-200">
                        {beneficialClauses.map((item) => (
                          <li key={item}>• {item}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {clauses.slice(0, 3).map((clause, index) => (
                    <ClauseCard key={clause.id} clause={clause} index={index} />
                  ))}
                </div>
              </div>

              <div className="space-y-6">
                {(yourObligations.length > 0 || otherPartyRights.length > 0) && (
                  <div className="section-card rounded-[30px] p-5 sm:p-6">
                    <h3 className="text-2xl font-semibold text-white">Rights & Obligations</h3>
                    <div className="mt-5 space-y-4">
                      {yourObligations.length > 0 && (
                        <div className="info-card rounded-[22px] p-4">
                          <p className="text-sm font-medium text-[#f5c26b]">Your Obligations</p>
                          <ul className="mt-3 space-y-2 text-sm leading-7 text-slate-300">
                            {yourObligations.map((item) => (
                              <li key={item}>• {item}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {otherPartyRights.length > 0 && (
                        <div className="info-card rounded-[22px] p-4">
                          <p className="text-sm font-medium text-[#c5b4ff]">Other Party Rights</p>
                          <ul className="mt-3 space-y-2 text-sm leading-7 text-slate-300">
                            {otherPartyRights.map((item) => (
                              <li key={item}>• {item}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {(summary.parties.length > 0 || summary.key_dates.length > 0) && (
                  <div className="section-card rounded-[30px] p-5 sm:p-6">
                    <h3 className="text-2xl font-semibold text-white">Parties & Dates</h3>
                    <div className="mt-5 grid gap-4">
                      {summary.parties.length > 0 && (
                        <div className="info-card rounded-[22px] p-4">
                          <p className="text-sm font-medium text-white">Parties</p>
                          <ul className="mt-3 space-y-2 text-sm leading-7 text-slate-300">
                            {summary.parties.map((party) => (
                              <li key={party}>• {party}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {summary.key_dates.length > 0 && (
                        <div className="info-card rounded-[22px] p-4">
                          <p className="text-sm font-medium text-white">Key Dates</p>
                          <ul className="mt-3 space-y-2 text-sm leading-7 text-slate-300">
                            {summary.key_dates.map((date) => (
                              <li key={`${date.label}-${date.date}`}>
                                <span className="text-slate-500">{date.label}:</span> {date.date}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}

          {activeTab === 'clauses' && (
            <section className="section-card rounded-[30px] p-5 sm:p-6">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-2xl font-semibold text-white">
                    {filter === 'all' ? `All Clauses (${clauses.length})` : `${filter} Risk Clauses (${filteredClauses.length})`}
                  </h3>
                  <p className="mt-2 text-sm text-slate-400">Filter and inspect every extracted clause from your document.</p>
                </div>

                <div className="flex flex-wrap gap-2">
                  {(['all', 'high', 'medium', 'low'] as FilterType[]).map((level) => (
                    <button
                      key={level}
                      type="button"
                      onClick={() => setFilter(level)}
                      className={`rounded-full border px-4 py-2 text-sm transition ${
                        filter === level
                          ? 'border-[#f5c26b]/25 bg-[#f5c26b]/10 text-[#f5c26b]'
                          : 'border-white/10 bg-white/[0.03] text-slate-400 hover:text-white'
                      }`}
                    >
                      {level === 'all' ? 'All' : level[0].toUpperCase() + level.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              <div className="mt-6 space-y-4">
                {clauses.length === 0 ? (
                  <div className="info-card rounded-[24px] px-5 py-10 text-center">
                    <p className="text-lg font-medium text-white">No clauses extracted yet</p>
                    <p className="mt-2 text-sm text-slate-400">The summary is available above, and you can still ask questions in the chat workspace.</p>
                    <button onClick={() => navigate('/chat')} className="btn-primary mt-6">
                      Ask AI
                    </button>
                  </div>
                ) : filteredClauses.length === 0 ? (
                  <div className="info-card rounded-[24px] px-5 py-10 text-center text-slate-400">
                    No clauses match this filter.
                  </div>
                ) : (
                  filteredClauses.map((clause, index) => (
                    <ClauseCard key={clause.id} clause={clause} index={index} />
                  ))
                )}
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  )
}
