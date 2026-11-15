import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import ClauseCard from '../components/ClauseCard'
import RiskBadge from '../components/RiskBadge'
import ConsequencesPanel from '../components/ConsequencesPanel'
import NegotiationPanel from '../components/NegotiationPanel'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { analyzeDocument, dropTranslation, translateAnalysis } from '../store/analysisSlice'
import { setInsightsDocument } from '../store/insightsSlice'
import { fetchDocumentById } from '../store/documentSlice'
import type { RiskLevel } from '../types'
import { trackEvent } from '../utils/posthog'
import { enumLabel, formatPercent, localizeKnownError } from '../utils/i18nHelpers'
import { exportAnalysisToPDF } from '../utils/pdfExporter'
import { buildVerdictView, isPartialResult, moneyAndDates, type VerdictT } from '../utils/analysisVerdict'
import { Card } from '../components/Card'
import { KeyRisks, MoneyDatesStrip, NextSteps, VerdictCard } from '../components/analysis/VerdictSection'
import { getDemoAnalysisResult, getDemoDocument } from '../utils/demoData'
import { getCurrentLang } from '../services/api'
import { LANGUAGES } from '../i18n/languages'
import { AnalysisProcessingProgress } from '../components/analysis/AnalysisProcessingProgress'
import { PartialAnalysisAlert } from '../components/analysis/PartialAnalysisAlert'
import { OptimizationBadge } from '../components/analysis/OptimizationBadge'
import { DocumentReadabilityBadge } from '../components/analysis/DocumentReadabilityBadge'
import { LegalDisclaimerBanner } from '../components/ui/LegalDisclaimerBanner'
import { LawyerEscalationModal } from '../components/ui/LawyerEscalationModal'

type FilterType = 'all' | RiskLevel

export default function Analysis({ isDemo = false }: { isDemo?: boolean }) {
  const { t, i18n } = useTranslation('analysis')
  // The language used to show analysis content follows the global app language. Static UI text comes
  // from i18n; AI-generated content (summary, clauses, risks, obligations, ...) is the base analysis
  // for English and the backend's AI-translated view (POST /analyze/{id}/translate) for hi / mr.
  const lang = getCurrentLang()
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { documentId } = useParams()

  const {
    result: apiResult,
    isLoading,
    error,
    state: analysisState,
    elapsedSeconds = 0,
    jobStage,
    jobProgress,
    translation,
  } = useAppSelector((s) => s.analysis)
  const apiDoc = useAppSelector((s) => s.document.current)

  const isDemoMode = isDemo || documentId === 'demo' || (!documentId && !apiDoc?.id && !apiResult)

  // Per-language translated view of the current document (hi / mr only; en uses the base analysis).
  const [showOriginal, setShowOriginal] = useState(false)
  const [translateAttempt, setTranslateAttempt] = useState(0)
  const translateKeyRef = useRef<string | null>(null)
  const wantsTranslation = !isDemoMode && lang !== 'en' && !showOriginal
  const translatedEntry =
    wantsTranslation && translation.documentId === documentId ? translation.byLang[lang] : undefined
  const translateFailed =
    wantsTranslation && !translatedEntry && translation.status === 'error' && translation.lang === lang
  const isTranslating = wantsTranslation && !translatedEntry && !translateFailed
  const demoResult = useMemo(() => getDemoAnalysisResult(lang), [lang])
  const demoDoc = useMemo(() => getDemoDocument(lang), [lang])

  const result = isDemoMode ? demoResult : translatedEntry ? translatedEntry.result : apiResult
  const currentDoc = isDemoMode ? demoDoc : apiDoc
  const languageName = LANGUAGES.find((l) => l.code === lang)?.nativeName ?? lang

  const [filter, setFilter] = useState<FilterType>('all')
  const [focusClauseId, setFocusClauseId] = useState<string | null>(null)
  const [isEscalationOpen, setIsEscalationOpen] = useState(false)
  const [activeNav, setActiveNav] = useState('overview')
  const requestedAnalysisRef = useRef<string | null>(null)
  const analyzeReqRef = useRef<{ abort: (reason?: string) => void } | null>(null)
  const trackedViewRef = useRef<string | null>(null)

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
    setFocusClauseId(null)
    setActiveNav('overview')
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

  // Language back to a translated one => leave the "show original" escape hatch.
  useEffect(() => {
    setShowOriginal(false)
  }, [lang, documentId])

  // Request the translated analysis when the app language is hi / mr (instant when cached server-side).
  useEffect(() => {
    if (isDemoMode || !documentId || lang === 'en' || showOriginal) return
    if (isLoading || !apiResult || apiResult.document_id !== documentId) return
    if (translation.documentId === documentId && translation.byLang[lang]) return
    // Translations were reset (new analysis result): forget the previous request key so we re-request.
    if (translation.documentId === null) translateKeyRef.current = null
    const key = `${documentId}:${lang}:${apiResult.analyzed_at ?? ''}:${translateAttempt}`
    if (translateKeyRef.current === key) return
    translateKeyRef.current = key
    dispatch(translateAnalysis({ documentId, lang }))
  }, [apiResult, dispatch, documentId, isDemoMode, isLoading, lang, showOriginal, translateAttempt, translation])

  const retryTranslation = () => {
    dispatch(dropTranslation(lang))
    setShowOriginal(false)
    setTranslateAttempt((n) => n + 1)
  }

  const isProcessing =
    !isDemoMode &&
    Boolean(documentId) &&
    !error &&
    (isLoading || !apiResult || apiResult.document_id !== documentId)

  if (isProcessing) {
    const isRetrying = analysisState === 'retrying_provider'
    return (
      <div className="content-wrap py-12 flex items-center justify-center min-h-[60vh]">
        <AnalysisProcessingProgress
          stage={
            analysisState === 'retrying_provider'
              ? 'retrying_provider'
              : analysisState === 'queued'
              ? 'queued'
              : 'processing'
          }
          statusMessage={
            isRetrying
              ? t('processing.retryingMessage')
              : undefined
          }
          elapsedSeconds={elapsedSeconds}
          jobStage={jobStage}
          jobProgress={jobProgress}
          onCancel={() => {
            analyzeReqRef.current?.abort()
            navigate('/upload')
          }}
        />
      </div>
    )
  }

  if (!isDemoMode && !documentId && !isLoading && !apiResult) return null

  if (!isDemoMode && error) {
    const isRateLimited =
      analysisState === 'provider_unavailable' ||
      error.toLowerCase().includes('rate limit') ||
      error.toLowerCase().includes('rate-limit') ||
      error.toLowerCase().includes('cooloff') ||
      error.toLowerCase().includes('capacity') ||
      error.toLowerCase().includes('too many concurrent')

    return (
      <div className="content-wrap py-8">
        <div className="section-card mx-auto max-w-2xl rounded-[32px] px-6 py-9 text-center space-y-4 shadow-2xl border border-white/10">
          <div
            className={`mx-auto flex h-20 w-20 items-center justify-center rounded-[28px] border text-3xl ${
              isRateLimited
                ? 'border-amber-400/30 bg-amber-400/10 text-amber-300'
                : 'border-[#fb7185]/20 bg-[#fb7185]/10 text-[#fecdd3]'
            }`}
            aria-hidden="true"
          >
            {isRateLimited ? '⏳' : '!'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-semibold text-white tracking-tight">
            {isRateLimited ? t('failed.capacityTitle') : t('failed.title')}
          </h1>
          <p className="mx-auto max-w-xl text-sm leading-7 text-slate-300">
            {isRateLimited ? t('failed.capacityBody') : localizeKnownError(t, error)}
          </p>
          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row pt-2">
            {documentId && (
              <button
                type="button"
                onClick={() => {
                  requestedAnalysisRef.current = documentId
                  dispatch(analyzeDocument({ documentId, forceReanalyze: true }))
                }}
                className="btn-primary min-h-[44px] px-6"
              >
                {isRateLimited ? t('failed.retryNow') : t('failed.retry')}
              </button>
            )}
            <button
              type="button"
              onClick={() => navigate('/upload')}
              className="btn-secondary min-h-[44px] px-6"
            >
              {t('failed.uploadAnother')}
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!isDemoMode && isTranslating) {
    return (
      <div className="content-wrap py-8">
        <div
          role="status"
          aria-live="polite"
          className="section-card mx-auto max-w-2xl rounded-[32px] px-6 py-9 text-center space-y-4 shadow-2xl border border-white/10"
        >
          <div className="mx-auto h-9 w-9 animate-spin rounded-full border-2 border-white/15 border-t-[#f5c26b]" />
          <h1 className="text-2xl sm:text-3xl font-semibold text-white tracking-tight">{t('translation.loadingTitle')}</h1>
          <p className="mx-auto max-w-xl text-sm leading-7 text-slate-300">
            {t('translation.loadingBody', { language: languageName })}
          </p>
          <div className="pt-2">
            <button type="button" onClick={() => setShowOriginal(true)} className="btn-secondary min-h-[44px] px-6">
              {t('translation.showOriginal')}
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!isDemoMode && translateFailed) {
    return (
      <div className="content-wrap py-8">
        <div className="section-card mx-auto max-w-2xl rounded-[32px] px-6 py-9 text-center space-y-4 shadow-2xl border border-white/10">
          <div
            className="mx-auto flex h-20 w-20 items-center justify-center rounded-[28px] border border-[#fb7185]/20 bg-[#fb7185]/10 text-3xl text-[#fecdd3]"
            aria-hidden="true"
          >
            !
          </div>
          <h1 className="text-2xl sm:text-3xl font-semibold text-white tracking-tight">{t('translation.failedTitle')}</h1>
          <p className="mx-auto max-w-xl text-sm leading-7 text-slate-300">{t('translation.failedBody')}</p>
          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row pt-2">
            <button type="button" onClick={retryTranslation} className="btn-primary min-h-[44px] px-6">
              {t('translation.retry')}
            </button>
            <button type="button" onClick={() => setShowOriginal(true)} className="btn-secondary min-h-[44px] px-6">
              {t('translation.showOriginal')}
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!result) return null

  const { summary, clauses } = result
  const isPartial = isPartialResult(result)
  const docTypeLabel = summary.document_type ? enumLabel(t, 'clauses:docTypes', summary.document_type) : ''
  const view = buildVerdictView(result, t as unknown as VerdictT, docTypeLabel)
  const moneyDates = moneyAndDates(result)

  const filteredClauses = filter === 'all' ? clauses : clauses.filter((c) => c.risk_level === filter)
  // Insight panels need a real, owned, analyzed document (not the public demo).
  const insightDocId = !isDemoMode && documentId && documentId !== 'demo' ? documentId : null

  const highRiskClauses: string[] = summary.high_risk_clauses || []
  const beneficialClauses: string[] = summary.beneficial_clauses || []
  const yourObligations: string[] = summary.your_obligations || []
  const otherPartyRights: string[] = summary.other_party_rights || []

  const exportPdf = () => {
    trackEvent('analysis_exported_pdf', { documentId: currentDoc?.id })
    void exportAnalysisToPDF(result, currentDoc, lang, { translated: Boolean(translatedEntry) })
  }

  const scrollToId = (id: string) => {
    requestAnimationFrame(() => {
      setTimeout(() => {
        document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 80)
    })
  }

  const jumpToClause = (index: number) => {
    const clause = clauses[index]
    if (!clause) return
    setFilter('all')
    setFocusClauseId(clause.id)
    setTimeout(() => {
      document.getElementById(`clause-${clause.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 120)
  }

  const showClauses = (level: FilterType) => {
    setFilter(level)
    setActiveNav('all-clauses')
    scrollToId('clauses-heading')
  }

  const reanalyze = () => {
    if (documentId) {
      requestedAnalysisRef.current = documentId
      dispatch(analyzeDocument({ documentId, forceReanalyze: true }))
    }
  }

  const goTo = (navId: string, targetId: string) => {
    setActiveNav(navId)
    scrollToId(targetId)
  }

  const sidebarConfig: Array<{
    id: string
    label: string
    onClick: () => void
  }> = [
    { id: 'overview', label: t('sidebar.nav.overview'), onClick: () => goTo('overview', 'overview-heading') },
    { id: 'key-points', label: t('sidebar.nav.keyPoints'), onClick: () => goTo('key-points', 'keypoints-heading') },
    { id: 'all-clauses', label: t('sidebar.nav.allClauses'), onClick: () => goTo('all-clauses', 'clauses-heading') },
    { id: 'risk-warnings', label: t('sidebar.nav.riskWarnings'), onClick: () => goTo('risk-warnings', 'risks-heading') },
    ...(insightDocId
      ? [
          { id: 'consequences', label: t('sidebar.nav.whatIfSign'), onClick: () => goTo('consequences', 'consequences-heading') },
          { id: 'negotiation', label: t('sidebar.nav.negotiate'), onClick: () => goTo('negotiation', 'negotiation-heading') },
        ]
      : []),
    { id: 'ask-ai', label: t('sidebar.nav.askAi'), onClick: () => navigate('/chat') },
  ]

  return (
    <div className="content-wrap py-5 sm:py-6">
      {isDemoMode && (
        <div className="mx-auto max-w-7xl mb-5">
          <Card variant="hero" className="rounded-[24px] border border-[#f5c26b]/30 bg-[#161208]/90 p-4 sm:p-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#f5c26b]/20 text-xl">✨</span>
                <div>
                  <p className="text-base font-semibold text-white">{t('demo.title')}</p>
                  <p className="text-xs text-slate-300">
                    {t('demo.body', { docType: enumLabel(t, 'clauses:docTypes', demoDoc.document_type ?? 'Residential Rental Agreement') })}
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
                {t('demo.cta')}
              </button>
            </div>
          </Card>
        </div>
      )}
      <div className="mx-auto grid max-w-7xl gap-6 xl:grid-cols-[260px_minmax(0,1fr)]">
        <Card as="aside" variant="section" className="h-fit rounded-[30px] p-5">
          <div className="mb-6">
            <p className="text-sm text-slate-500">{t('sidebar.eyebrow')}</p>
            <h1 className="mt-2 text-2xl font-semibold text-white">{t('sidebar.title')}</h1>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              {currentDoc?.filename || t('sidebar.fallbackDoc')}
            </p>
          </div>

          <div className="space-y-2">
            {sidebarConfig.map((item, index) => (
              <button
                key={item.id}
                type="button"
                onClick={item.onClick}
                className={`flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm transition ${
                  activeNav === item.id
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
              onClick={exportPdf}
              className="btn-secondary w-full justify-center gap-2 py-3 text-xs"
            >
              <span>📥</span> {t('sidebar.exportPdf')}
            </button>
          </div>
        </Card>

        <div className="space-y-6">
          {!isDemoMode && lang !== 'en' && showOriginal && (
            <div className="info-card rounded-[24px] p-4 text-sm text-slate-300">
              <p>{t('translation.originalNotice')}</p>
              <button type="button" onClick={retryTranslation} className="btn-secondary mt-3 px-4 py-2.5 text-xs">
                {t('translation.translateNow', { language: languageName })}
              </button>
            </div>
          )}

          {translatedEntry?.partial && (
            <div className="rounded-[24px] border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-200">
              <p>{t('translation.partialBody', { language: languageName })}</p>
              <button type="button" onClick={retryTranslation} className="btn-secondary mt-3 px-4 py-2.5 text-xs">
                {t('translation.partialRetry')}
              </button>
            </div>
          )}

          {translatedEntry && !translatedEntry.partial && (
            <p className="px-1 text-xs text-slate-500">{t('translation.aiNote', { language: languageName })}</p>
          )}

          {isPartial && (
            <PartialAnalysisAlert
              completionRatio={result.metadata?.completion_ratio}
              totalChunks={result.metadata?.total_chunks}
              successfulChunks={result.metadata?.successful_chunks}
              incompleteChunks={result.metadata?.incomplete_chunks}
              onReanalyze={reanalyze}
              onAskAdvocate={() => setIsEscalationOpen(true)}
              isReanalyzing={isLoading}
            />
          )}

          {/* Risk counts (click High or Medium to show only those clauses) */}
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4" role="group" aria-label={t('overview.title')}>
            <div className="metric-card rounded-[22px] p-4">
              <p className="text-3xl font-semibold text-white">{summary.total_clauses}</p>
              <p className="mt-1 text-sm text-slate-400">{t('metrics.total')}</p>
            </div>
            <button
              type="button"
              onClick={() => showClauses('high')}
              className="metric-card rounded-[22px] p-4 text-left transition hover:border-[#fb7185]/25"
            >
              <p className="text-3xl font-semibold text-[#fb7185]">{summary.high_risk_count}</p>
              <p className="mt-1 text-sm text-slate-400">{t('metrics.high')}</p>
            </button>
            <button
              type="button"
              onClick={() => showClauses('medium')}
              className="metric-card rounded-[22px] p-4 text-left transition hover:border-[#f5c26b]/25"
            >
              <p className="text-3xl font-semibold text-[#f5c26b]">{summary.medium_risk_count}</p>
              <p className="mt-1 text-sm text-slate-400">{t('metrics.medium')}</p>
            </button>
            <div className="metric-card rounded-[22px] p-4">
              <RiskBadge level={summary.overall_risk} />
              <p className="mt-2 text-sm leading-6 text-slate-400">
                {isPartial ? (
                  <span>
                    {t('metrics.preliminary')}{' '}
                    {result.metadata?.completion_ratio != null ? (
                      <span className="text-amber-400 text-xs font-semibold">
                        {t('metrics.analyzedPct', { pct: formatPercent(result.metadata.completion_ratio, i18n.language) })}
                      </span>
                    ) : (
                      <span className="text-amber-400 text-xs font-semibold">{t('metrics.partial')}</span>
                    )}
                  </span>
                ) : (
                  t('metrics.overall')
                )}
              </p>
            </div>
          </div>

          {/* 1) Verdict */}
          <VerdictCard view={view} />

          {/* 2) Three key risks + 3) what to do next */}
          <KeyRisks view={view} onJump={jumpToClause} />
          <NextSteps view={view} onLawyer={() => setIsEscalationOpen(true)} />

          {/* 4) Full clause list */}
          <Card as="section" variant="section" aria-labelledby="clauses-heading" className="scroll-mt-28 rounded-[30px] p-5 sm:p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 id="clauses-heading" className="scroll-mt-28 text-2xl font-semibold text-white">
                  {filter === 'all'
                    ? t('clausesSection.titleAll', { count: clauses.length })
                    : t(`clausesSection.title${filter[0].toUpperCase()}${filter.slice(1)}`, { count: filteredClauses.length })}
                </h3>
                <p className="mt-2 text-sm text-slate-400">{t('clausesSection.subtitle')}</p>
              </div>

              <div role="group" aria-label={t('clausesSection.subtitle')} className="flex flex-wrap gap-2">
                {(['all', 'high', 'medium', 'low'] as FilterType[]).map((level) => (
                  <button
                    key={level}
                    type="button"
                    aria-pressed={filter === level}
                    onClick={() => setFilter(level)}
                    className={`rounded-full border px-4 py-2 text-sm transition ${
                      filter === level
                        ? 'border-[#f5c26b]/25 bg-[#f5c26b]/10 text-[#f5c26b]'
                        : 'border-white/10 bg-white/[0.03] text-slate-400 hover:text-white'
                    }`}
                  >
                    {level === 'all' ? t('clausesSection.filterAll') : t(`clauses:riskShort.${level}`)}
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-6 space-y-4">
              {clauses.length === 0 ? (
                <div className="info-card rounded-[24px] px-5 py-10 text-center">
                  <p className="text-lg font-medium text-white">{t('clausesSection.emptyTitle')}</p>
                  <p className="mt-2 text-sm text-slate-400">{t('clausesSection.emptyBody')}</p>
                  <button onClick={() => navigate('/chat')} className="btn-primary mt-6">
                    {t('clausesSection.askAi')}
                  </button>
                </div>
              ) : filteredClauses.length === 0 ? (
                <div className="info-card rounded-[24px] px-5 py-10 text-center text-slate-400">
                  {t('clausesSection.noMatch')}
                </div>
              ) : (
                filteredClauses.map((clause, index) => (
                  <ClauseCard key={clause.id} clause={clause} index={index} forceOpen={clause.id === focusClauseId} />
                ))
              )}
            </div>
          </Card>

          {/* Remaining original sections */}
          <Card as="section" variant="section" aria-labelledby="summary-heading" className="scroll-mt-28 rounded-[30px] p-5 sm:p-6">
            <h3 id="summary-heading" className="text-2xl font-semibold text-white">
              {t('aiSummary')}
            </h3>
            {summary.risk_summary && <p className="mt-3 text-sm leading-7 text-slate-300">{summary.risk_summary}</p>}
          </Card>

          <MoneyDatesStrip data={moneyDates} />

          <Card as="section" variant="section" aria-labelledby="overview-heading" className="scroll-mt-28 rounded-[30px] p-5 sm:p-6">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <p className="text-sm text-slate-500">
                  {t('overview.documentLabel', { name: currentDoc?.filename || t('overview.fallbackFilename') })}
                </p>
                <div className="mt-1 flex flex-wrap items-center gap-3">
                  <h2 id="overview-heading" className="scroll-mt-28 text-2xl font-semibold text-white">
                    {t('overview.title')}
                  </h2>
                  <DocumentReadabilityBadge
                    pageType={
                      result.metadata?.page_types
                        ? Object.values(result.metadata.page_types).includes('scanned')
                          ? 'scanned'
                          : 'digital'
                        : 'digital'
                    }
                    qualityScore={result.metadata?.quality_score}
                    ocrConfidence={result.metadata?.ocr_confidence}
                  />
                  {result.metadata?.optimization && (
                    <OptimizationBadge optimization={result.metadata.optimization} />
                  )}
                </div>
                <p className="mt-1.5 text-sm leading-6 text-slate-400">{t('overview.intro')}</p>
              </div>
              <div className="flex flex-col gap-2.5 sm:min-w-[280px] shrink-0">
                {/* 1st Row: Primary Highlighted Button */}
                <button onClick={() => navigate('/chat')} className="btn-primary w-full justify-center">
                  {t('overview.askAbout')}
                </button>

                {/* 2nd Row: Upload Another & Export PDF */}
                <div className="grid grid-cols-2 gap-2">
                  <button onClick={() => navigate('/upload')} className="btn-secondary justify-center px-3 py-2.5 text-xs">
                    {t('overview.uploadAnother')}
                  </button>
                  <button
                    type="button"
                    onClick={exportPdf}
                    className="btn-secondary justify-center px-3 py-2.5 text-xs flex items-center gap-1.5"
                  >
                    <span>📥</span> {t('overview.exportPdf')}
                  </button>
                </div>
              </div>
            </div>

            <div className="mt-5">
              <div className="info-card rounded-[24px] p-5">
                <p className="text-sm font-medium text-white">{t('details.title')}</p>
                <div className="mt-4 space-y-3 text-sm text-slate-300">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-slate-500">{t('details.type')}</span>
                    <span>{docTypeLabel}</span>
                  </div>
                  {summary.language && (
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-slate-500">{t('details.language')}</span>
                      <span>{enumLabel(t, 'clauses:languages', summary.language)}</span>
                    </div>
                  )}
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-slate-500">{t('details.parties')}</span>
                    <span>{summary.parties.length || 0}</span>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-slate-500">{t('details.keyDates')}</span>
                    <span>{summary.key_dates.length || 0}</span>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          <section className="grid scroll-mt-28 gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <Card variant="section" className="rounded-[30px] p-5 sm:p-6">
              <div className="mb-5 flex items-center justify-between gap-4">
                <h3 id="keypoints-heading" className="scroll-mt-28 text-2xl font-semibold text-white">
                  {t('keyPoints.title')}
                </h3>
                <button type="button" onClick={() => showClauses('all')} className="btn-secondary px-4 py-2.5 text-sm">
                  {t('keyPoints.viewAll')}
                </button>
              </div>

              <div className="space-y-4">
                {highRiskClauses.length > 0 && (
                  <div className="rounded-[24px] border border-[#fb7185]/18 bg-[#2a1320]/55 p-5">
                    <p className="text-sm font-medium text-[#fecdd3]">{t('keyPoints.highRisk')}</p>
                    <ul className="mt-3 space-y-2 text-sm leading-7 text-slate-200">
                      {highRiskClauses.map((item) => (
                        <li key={item}>• {item}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {beneficialClauses.length > 0 && (
                  <div className="rounded-[24px] border border-[#34d399]/18 bg-[#10241f]/55 p-5">
                    <p className="text-sm font-medium text-[#bbf7d0]">{t('keyPoints.protect')}</p>
                    <ul className="mt-3 space-y-2 text-sm leading-7 text-slate-200">
                      {beneficialClauses.map((item) => (
                        <li key={item}>• {item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Card>

            <div className="space-y-6">
              {(yourObligations.length > 0 || otherPartyRights.length > 0) && (
                <Card variant="section" className="rounded-[30px] p-5 sm:p-6">
                  <h3 className="text-2xl font-semibold text-white">{t('rights.title')}</h3>
                  <div className="mt-5 space-y-4">
                    {yourObligations.length > 0 && (
                      <div className="info-card rounded-[22px] p-4">
                        <p className="text-sm font-medium text-[#f5c26b]">{t('rights.yours')}</p>
                        <ul className="mt-3 space-y-2 text-sm leading-7 text-slate-300">
                          {yourObligations.map((item) => (
                            <li key={item}>• {item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {otherPartyRights.length > 0 && (
                      <div className="info-card rounded-[22px] p-4">
                        <p className="text-sm font-medium text-[#c5b4ff]">{t('rights.other')}</p>
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
                  <h3 className="text-2xl font-semibold text-white">{t('partiesDates.title')}</h3>
                  <div className="mt-5 grid gap-4">
                    {summary.parties.length > 0 && (
                      <div className="info-card rounded-[22px] p-4">
                        <p className="text-sm font-medium text-white">{t('partiesDates.parties')}</p>
                        <ul className="mt-3 space-y-2 text-sm leading-7 text-slate-300">
                          {summary.parties.map((party) => (
                            <li key={party}>• {party}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {summary.key_dates.length > 0 && (
                      <div className="info-card rounded-[22px] p-4">
                        <p className="text-sm font-medium text-white">{t('partiesDates.keyDates')}</p>
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

          {insightDocId && (
            <Card as="section" variant="section" aria-labelledby="consequences-heading" className="scroll-mt-28 rounded-[30px] p-5 sm:p-6">
              <div className="mb-4">
                <h3 id="consequences-heading" className="scroll-mt-28 text-2xl font-semibold text-white">
                  {t('consequencesSection.title')}
                </h3>
                <p className="mt-2 text-sm text-slate-400">{t('consequencesSection.subtitle')}</p>
              </div>
              <ConsequencesPanel documentId={insightDocId} />
            </Card>
          )}

          {insightDocId && (
            <Card as="section" variant="section" aria-labelledby="negotiation-heading" className="scroll-mt-28 rounded-[30px] p-5 sm:p-6">
              <div className="mb-4">
                <h3 id="negotiation-heading" className="scroll-mt-28 text-2xl font-semibold text-white">
                  {t('negotiationSection.title')}
                </h3>
                <p className="mt-2 text-sm text-slate-400">{t('negotiationSection.subtitle')}</p>
              </div>
              <NegotiationPanel documentId={insightDocId} />
            </Card>
          )}

          <div className="mt-8">
            <LegalDisclaimerBanner />
          </div>
        </div>
      </div>

      <LawyerEscalationModal
        isOpen={isEscalationOpen}
        onClose={() => setIsEscalationOpen(false)}
        documentName={currentDoc?.filename || ''}
      />
    </div>
  )
}
