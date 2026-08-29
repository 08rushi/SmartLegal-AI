import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ClauseCard from '../components/ClauseCard'
import RiskBadge from '../components/RiskBadge'
import ConsequencesPanel from '../components/ConsequencesPanel'
import NegotiationPanel from '../components/NegotiationPanel'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { analyzeDocument } from '../store/analysisSlice'
import { setInsightsDocument } from '../store/insightsSlice'
import { fetchDocumentById } from '../store/documentSlice'
import type { RiskLevel } from '../types'
import { trackEvent } from '../utils/posthog'
import { Card } from '../components/Card'
import { exportAnalysisToPDF } from '../utils/pdfExporter'
import { demoAnalysisResult, demoDocument } from '../utils/demoData'

type FilterType = 'all' | RiskLevel
type ActiveTab = 'summary' | 'clauses' | 'consequences' | 'negotiation'

function AnalysisSkeleton() {
  return (
    <div className="content-wrap py-6">
      <div className="mx-auto grid max-w-7xl gap-6 xl:grid-cols-[260px_minmax(0,1fr)]">
        <aside className="section-card rounded-[30px] p-5">
          <div className="skeleton-block h-4 w-28 rounded-full" />
          <div className="mt-4 skeleton-block h-8 w-40 rounded-2xl" />
          <div className="mt-3 skeleton-block h-16 w-full rounded-2xl" />
          <div className="mt-6 space-y-3">
            {[1, 2, 3, 4, 5].map((item) => (
              <div key={item} className="skeleton-block h-12 w-full rounded-2xl" />
            ))}
          </div>
        </aside>

        <div className="space-y-6">
          <section className="section-card rounded-[30px] p-5 sm:p-7">
            <div className="flex flex-col gap-4 lg:flex-row lg:justify-between">
              <div className="flex-1">
                <div className="skeleton-block h-4 w-40 rounded-full" />
                <div className="mt-4 skeleton-block h-10 w-56 rounded-2xl" />
                <div className="mt-3 skeleton-block h-16 w-full rounded-2xl" />
              </div>
              <div className="flex gap-3">
                <div className="skeleton-block h-11 w-44 rounded-2xl" />
                <div className="skeleton-block h-11 w-36 rounded-2xl" />
              </div>
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {[1, 2, 3, 4].map((item) => (
                <div key={item} className="metric-card rounded-[22px] p-4">
                  <div className="skeleton-block h-10 w-16 rounded-2xl" />
                  <div className="mt-3 skeleton-block h-4 w-24 rounded-full" />
                </div>
              ))}
            </div>

            <div className="mt-5 grid gap-3 xl:grid-cols-[1.15fr_0.85fr]">
              <div className="info-card rounded-[24px] p-5">
                <div className="skeleton-block h-4 w-24 rounded-full" />
                <div className="mt-4 space-y-3">
                  <div className="skeleton-block h-4 w-full rounded-full" />
                  <div className="skeleton-block h-4 w-11/12 rounded-full" />
                  <div className="skeleton-block h-4 w-4/5 rounded-full" />
                </div>
              </div>
              <div className="info-card rounded-[24px] p-5">
                <div className="skeleton-block h-4 w-32 rounded-full" />
                <div className="mt-4 space-y-4">
                  {[1, 2, 3].map((row) => (
                    <div key={row} className="flex items-center justify-between gap-3">
                      <div className="skeleton-block h-4 w-20 rounded-full" />
                      <div className="skeleton-block h-4 w-24 rounded-full" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="section-card rounded-[30px] p-5 sm:p-6">
            <div className="space-y-4">
              {[1, 2, 3].map((item) => (
                <div key={item} className="info-card rounded-[24px] p-5">
                  <div className="skeleton-block h-5 w-40 rounded-full" />
                  <div className="mt-4 space-y-3">
                    <div className="skeleton-block h-4 w-full rounded-full" />
                    <div className="skeleton-block h-4 w-10/12 rounded-full" />
                    <div className="skeleton-block h-4 w-9/12 rounded-full" />
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}

export default function Analysis({ isDemo = false }: { isDemo?: boolean }) {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { documentId } = useParams()
  
  const { result: apiResult, isLoading, error } = useAppSelector((s) => s.analysis)
  const apiDoc = useAppSelector((s) => s.document.current)

  const isDemoMode = isDemo || documentId === 'demo' || (!documentId && !apiDoc?.id && !apiResult)

  const result = isDemoMode ? demoAnalysisResult : apiResult
  const currentDoc = isDemoMode ? demoDocument : apiDoc

  const [filter, setFilter] = useState<FilterType>('all')
  const [activeTab, setActiveTab] = useState<ActiveTab>('summary')
  const requestedAnalysisRef = useRef<string | null>(null)
  const analyzeReqRef = useRef<{ abort: (reason?: string) => void } | null>(null)
  const trackedViewRef = useRef<string | null>(null)
  const overviewRef = useRef<HTMLElement | null>(null)
  const keyPointsRef = useRef<HTMLElement | null>(null)
  const riskWarningsRef = useRef<HTMLDivElement | null>(null)
  const clausesRef = useRef<HTMLElement | null>(null)
  const consequencesRef = useRef<HTMLElement | null>(null)
  const negotiationRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (isDemoMode) return

    if (!documentId) {
      if (apiDoc?.id) {
        navigate(`/analysis/${apiDoc.id}`, { replace: true })
        return
      }

      if (!isLoading && !apiResult) {
        navigate('/upload', { replace: true })
      }
      return
    }

    if (apiDoc?.id !== documentId) {
      dispatch(fetchDocumentById(documentId))
    }

    if (!isLoading && apiResult?.document_id !== documentId && requestedAnalysisRef.current !== documentId) {
      requestedAnalysisRef.current = documentId
      analyzeReqRef.current = dispatch(analyzeDocument(documentId))
    }
  }, [apiDoc?.id, apiResult, dispatch, documentId, isDemoMode, isLoading, navigate])

  // Cancel the in-flight analysis poll when the document changes or on unmount,
  // so the 3s status loop doesn't keep running (up to 5 min) after navigating away.
  useEffect(() => {
    return () => {
      analyzeReqRef.current?.abort()
      analyzeReqRef.current = null
      requestedAnalysisRef.current = null
    }
  }, [documentId])

  useEffect(() => {
    requestedAnalysisRef.current = null
    setFilter('all')
    setActiveTab('summary')
    if (documentId && documentId !== 'demo') {
      dispatch(setInsightsDocument(documentId))
    }
  }, [documentId, dispatch])

  useEffect(() => {
    if (result?.document_id && trackedViewRef.current !== result.document_id) {
      trackedViewRef.current = result.document_id
      trackEvent('analysis_viewed', {
        documentId: result.document_id,
        clauseCount: result.summary.total_clauses,
        overallRisk: result.summary.overall_risk,
      })
    }
  }, [result])

  type SectionKey = 'overview' | 'key-points' | 'all-clauses' | 'risk-warnings' | 'consequences' | 'negotiation'

  const sectionMap: Record<SectionKey, { tab: ActiveTab; ref: React.RefObject<HTMLElement | HTMLDivElement | null> }> = {
    overview: { tab: 'summary', ref: overviewRef },
    'key-points': { tab: 'summary', ref: keyPointsRef },
    'all-clauses': { tab: 'clauses', ref: clausesRef },
    'risk-warnings': { tab: 'summary', ref: riskWarningsRef },
    consequences: { tab: 'consequences', ref: consequencesRef },
    negotiation: { tab: 'negotiation', ref: negotiationRef },
  }

  const scrollToSection = (section: SectionKey) => {
    const config = sectionMap[section]
    if (!config) return
    setActiveTab(config.tab)
    requestAnimationFrame(() => {
      setTimeout(() => {
        const target = config.ref.current || (section === 'risk-warnings' ? keyPointsRef.current : null)
        target?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 80)
    })
  }

  const shouldShowSkeleton =
    !isDemoMode &&
    Boolean(documentId) &&
    !error &&
    (isLoading || !apiResult || apiResult.document_id !== documentId)

  if (shouldShowSkeleton) {
    return <AnalysisSkeleton />
  }


  if (!isDemoMode && !documentId && !isLoading && !apiResult) return null

  if (!isDemoMode && error) {
    return (
      <div className="content-wrap py-6">
        <div className="section-card mx-auto max-w-3xl rounded-[32px] px-6 py-9 text-center">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-[28px] border border-[#fb7185]/20 bg-[#fb7185]/10 text-3xl text-[#fecdd3]">
            !
          </div>
          <h1 className="mt-6 text-3xl font-semibold text-white">Analysis Failed</h1>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-slate-400">{error}</p>
          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            {documentId && (
              <button
                type="button"
                onClick={() => {
                  requestedAnalysisRef.current = documentId
                  dispatch(analyzeDocument({ documentId, forceReanalyze: true }))
                }}
                className="btn-primary"
              >
                Retry Analysis
              </button>
            )}
            <button type="button" onClick={() => navigate('/upload')} className="btn-secondary">
              Upload Another
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!result) return null

  const { summary, clauses } = result
  const filteredClauses = filter === 'all' ? clauses : clauses.filter((c) => c.risk_level === filter)
  // Insight tabs need a real, owned, analyzed document (not the public demo).
  const insightDocId = !isDemoMode && documentId && documentId !== 'demo' ? documentId : null

  const sidebarConfig: Array<{
    id: string
    label: string
    isActive: boolean
    onClick: () => void
  }> = [
    { id: 'overview', label: 'Overview', isActive: activeTab === 'summary', onClick: () => scrollToSection('overview') },
    { id: 'key-points', label: 'Key Points', isActive: activeTab === 'summary', onClick: () => scrollToSection('key-points') },
    { id: 'all-clauses', label: 'All Clauses', isActive: activeTab === 'clauses', onClick: () => scrollToSection('all-clauses') },
    { id: 'risk-warnings', label: 'Risk Warnings', isActive: activeTab === 'summary', onClick: () => scrollToSection('risk-warnings') },
    ...(insightDocId ? [
      { id: 'consequences', label: 'What If I Sign', isActive: activeTab === 'consequences', onClick: () => scrollToSection('consequences') },
      { id: 'negotiation', label: 'Negotiate', isActive: activeTab === 'negotiation', onClick: () => scrollToSection('negotiation') },
    ] : []),
    { id: 'ask-ai', label: 'Ask AI', isActive: false, onClick: () => navigate('/chat') },
  ]

  const highRiskClauses: string[] = summary.high_risk_clauses || []
  const beneficialClauses: string[] = summary.beneficial_clauses || []
  const yourObligations: string[] = summary.your_obligations || []
  const otherPartyRights: string[] = summary.other_party_rights || []

  return (
    <div className="content-wrap py-5 sm:py-6">
      {isDemoMode && (
        <div className="mx-auto max-w-7xl mb-5">
          <Card variant="hero" className="rounded-[24px] border border-[#f5c26b]/30 bg-[#161208]/90 p-4 sm:p-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#f5c26b]/20 text-xl">✨</span>
                <div>
                  <p className="text-base font-semibold text-white">Interactive Demo Analysis Mode</p>
                  <p className="text-xs text-slate-300">
                    Viewing sample AI risk review for a <span className="font-semibold text-[#f5c26b]">Residential Rental Agreement</span>. Try switching tabs, toggling Hindi translation, or downloading the PDF report!
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  window.scrollTo(0, 0)
                  navigate('/upload')
                }}
                className="btn-primary text-xs px-5 py-2.5 self-start sm:self-auto shrink-0 shadow-lg"
              >
                Upload Your Document →
              </button>
            </div>
          </Card>
        </div>
      )}
      <div className="mx-auto grid max-w-7xl gap-6 xl:grid-cols-[260px_minmax(0,1fr)]">
        <Card as="aside" variant="section" className="h-fit rounded-[30px] p-5">
          <div className="mb-6">
            <p className="text-sm text-slate-500">Analysis Overview</p>
            <h1 className="mt-2 text-2xl font-semibold text-white">Document Review</h1>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              {currentDoc?.filename || 'Uploaded document'}
            </p>
          </div>

          <div className="space-y-2">
            {sidebarConfig.map((item, index) => (
              <button
                key={item.id}
                type="button"
                onClick={item.onClick}
                className={`flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm transition ${
                  item.isActive
                    ? 'bg-white/10 text-[#f5c26b]'
                    : 'text-slate-400 hover:bg-white/[0.03] hover:text-white'
                }`}
              >
                <span className="text-xs text-slate-500">{String(index + 1).padStart(2, '0')}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </div>

          <div className="mt-6 border-t border-white/10 pt-4">
            <button
              type="button"
              onClick={() => {
                trackEvent('analysis_exported_pdf', { documentId: currentDoc?.id })
                exportAnalysisToPDF(result, currentDoc)
              }}
              className="btn-secondary w-full justify-center gap-2 py-3 text-xs"
            >
              <span>📥</span> Export PDF Report
            </button>
          </div>
        </Card>

        <div className="space-y-6">
          <Card as="section" ref={overviewRef} variant="section" className="scroll-mt-28 rounded-[30px] p-5 sm:p-6">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <p className="text-sm text-slate-500">Document: {currentDoc?.filename || 'Legal Agreement.pdf'}</p>
                <h2 className="mt-1 text-2xl font-semibold text-white">Analysis Overview</h2>
                <p className="mt-1.5 text-sm leading-6 text-slate-400">
                  Review risk counts, core obligations, and your contract summary in one structured dashboard.
                </p>
              </div>
              <div className="flex flex-col gap-2.5 sm:min-w-[280px] shrink-0">
                {/* 1st Row: Primary Highlighted Button */}
                <button onClick={() => navigate('/chat')} className="btn-primary w-full justify-center">
                  Ask About This Document →
                </button>

                {/* 2nd Row: Upload Another & Export PDF */}
                <div className="grid grid-cols-2 gap-2">
                  <button onClick={() => navigate('/upload')} className="btn-secondary justify-center px-3 py-2.5 text-xs">
                    Upload Another
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      trackEvent('analysis_exported_pdf', { documentId: currentDoc?.id })
                      exportAnalysisToPDF(result, currentDoc)
                    }}
                    className="btn-secondary justify-center px-3 py-2.5 text-xs flex items-center gap-1.5"
                  >
                    <span>📥</span> Export PDF
                  </button>
                </div>
              </div>
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <div className="metric-card rounded-[22px] p-4">
                <p className="text-3xl font-semibold text-white">{summary.total_clauses}</p>
                <p className="mt-1 text-sm text-slate-400">Total clauses</p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setFilter('high')
                  setActiveTab('clauses')
                  scrollToSection('all-clauses')
                }}
                className="metric-card rounded-[22px] p-4 text-left transition hover:border-[#fb7185]/25"
              >
                <p className="text-3xl font-semibold text-[#fb7185]">{summary.high_risk_count}</p>
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
                <p className="text-3xl font-semibold text-[#f5c26b]">{summary.medium_risk_count}</p>
                <p className="mt-1 text-sm text-slate-400">Medium risk items</p>
              </button>
              <div className="metric-card rounded-[22px] p-4">
                <RiskBadge level={summary.overall_risk} />
                <p className="mt-2 text-sm leading-6 text-slate-400">Overall contract risk profile</p>
              </div>
            </div>

            <div className="mt-5 grid gap-3 xl:grid-cols-[1.15fr_0.85fr]">
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
                  {summary.language && (
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-slate-500">Language</span>
                      <span>{summary.language}</span>
                    </div>
                  )}
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
          </Card>

          {activeTab === 'summary' && (
            <section ref={keyPointsRef} className="grid scroll-mt-28 gap-6 xl:grid-cols-[1.15fr_0.85fr]">
              <Card variant="section" className="rounded-[30px] p-5 sm:p-6">
                <div className="mb-5 flex items-center justify-between gap-4">
                  <h3 className="text-2xl font-semibold text-white">Key Points</h3>
                  <button type="button" onClick={() => setActiveTab('clauses')} className="btn-secondary px-4 py-2.5 text-sm">
                    View All Clauses
                  </button>
                </div>

                <div className="space-y-4">
                  {highRiskClauses.length > 0 && (
                    <div ref={riskWarningsRef} className="rounded-[24px] border border-[#fb7185]/18 bg-[#2a1320]/55 p-5">
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
              </Card>

              <div className="space-y-6">
                {(yourObligations.length > 0 || otherPartyRights.length > 0) && (
                  <Card variant="section" className="rounded-[30px] p-5 sm:p-6">
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
                  </Card>
                )}

                {(summary.parties.length > 0 || summary.key_dates.length > 0) && (
                  <Card variant="section" className="rounded-[30px] p-5 sm:p-6">
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
                  </Card>
                )}
              </div>
            </section>
          )}

          {activeTab === 'clauses' && (
            <Card as="section" ref={clausesRef} variant="section" className="scroll-mt-28 rounded-[30px] p-5 sm:p-6">
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
            </Card>
          )}

          {activeTab === 'consequences' && insightDocId && (
            <Card as="section" ref={consequencesRef} variant="section" className="scroll-mt-28 rounded-[30px] p-5 sm:p-6">
              <div className="mb-4">
                <h3 className="text-2xl font-semibold text-white">What Happens If I Sign?</h3>
                <p className="mt-2 text-sm text-slate-400">
                  A realistic simulation of the consequences you could face if you sign this document as-is.
                </p>
              </div>
              <ConsequencesPanel documentId={insightDocId} />
            </Card>
          )}

          {activeTab === 'negotiation' && insightDocId && (
            <Card as="section" ref={negotiationRef} variant="section" className="scroll-mt-28 rounded-[30px] p-5 sm:p-6">
              <div className="mb-4">
                <h3 className="text-2xl font-semibold text-white">Negotiate Better Terms</h3>
                <p className="mt-2 text-sm text-slate-400">
                  Safer alternatives and copy-ready counter-wording for the clauses that are risky for you.
                </p>
              </div>
              <NegotiationPanel documentId={insightDocId} />
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
