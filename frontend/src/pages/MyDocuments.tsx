import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { analyzeDocument } from '../store/analysisSlice'
import { clearDocument, setCurrentDocument } from '../store/documentSlice'
import type { UploadedDocument } from '../types'
import { trackEvent } from '../utils/posthog'

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

function DocTypeIcon({ type }: { type: string }) {
  const t = type.toLowerCase()
  if (t.includes('rent') || t.includes('lease')) return <span>🏠</span>
  if (t.includes('employ') || t.includes('work')) return <span>💼</span>
  if (t.includes('loan') || t.includes('borrow')) return <span>🏦</span>
  if (t.includes('service') || t.includes('contract')) return <span>📋</span>
  return <span>📄</span>
}

export default function MyDocuments() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { history, current } = useAppSelector((s) => s.document)
  const { result, isLoading } = useAppSelector((s) => s.analysis)
  const { user, token } = useAppSelector((s) => s.auth)

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!token) {
      navigate('/login')
    }
  }, [token, navigate])

  async function handleReAnalyze(doc: UploadedDocument) {
    dispatch(setCurrentDocument(doc))
    trackEvent('document_reanalyze_started', { documentId: doc.id })
    await dispatch(analyzeDocument(doc.id))
    navigate(`/analysis/${doc.id}`)
  }

  function handleClearAndUpload() {
    dispatch(clearDocument())
    navigate('/upload')
  }

  if (!token) return null

  return (
    <div className="content-wrap py-8 sm:py-10">
      <div className="mx-auto max-w-7xl">

        {/* Header */}
        <div className="section-card rounded-[32px] p-6 sm:p-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <span className="section-eyebrow">Document History</span>
              <h1 className="mt-4 text-3xl font-semibold text-white sm:text-4xl">My Documents</h1>
              <p className="mt-2 text-sm leading-7 text-slate-400">
                {user ? `Signed in as ${user.name} (${user.email})` : 'All your uploaded and analyzed documents in one place.'}
              </p>
            </div>
            <button onClick={handleClearAndUpload} className="btn-primary px-5 py-3">
              + Upload New Document
            </button>
          </div>

          {/* Stats bar */}
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <div className="metric-card rounded-[22px] px-5 py-4">
              <p className="text-3xl font-semibold text-white">{history.length}</p>
              <p className="mt-1 text-sm text-slate-400">Documents analyzed</p>
            </div>
            <div className="metric-card rounded-[22px] px-5 py-4">
              <p className="text-3xl font-semibold text-[#f5c26b]">
                {result ? result.summary.high_risk_count : '—'}
              </p>
              <p className="mt-1 text-sm text-slate-400">High risk clauses (last doc)</p>
            </div>
            <div className="metric-card rounded-[22px] px-5 py-4">
              <p className="text-3xl font-semibold text-[#34d399]">
                {result ? result.summary.total_clauses : '—'}
              </p>
              <p className="mt-1 text-sm text-slate-400">Clauses extracted (last doc)</p>
            </div>
          </div>
        </div>

        {/* Document list */}
        <div className="mt-6 section-card rounded-[32px] p-5 sm:p-7">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-xl font-semibold text-white">Recent Documents</h2>
            <span className="text-sm text-slate-500">{history.length} total</span>
          </div>

          {history.length === 0 ? (
            /* Empty state */
            <div className="flex flex-col items-center gap-5 py-16 text-center">
              <div className="flex h-24 w-24 items-center justify-center rounded-[30px] border border-white/10 bg-white/[0.03] text-4xl">
                📂
              </div>
              <div>
                <h3 className="text-xl font-semibold text-white">No documents yet</h3>
                <p className="mt-2 max-w-sm text-sm leading-7 text-slate-400">
                  Upload your first contract, rental agreement, or legal document to get started.
                </p>
              </div>
              <Link to="/upload" className="btn-primary px-6 py-3">
                Upload a Document →
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {history.map((doc) => {
                const isCurrent = doc.id === current?.id
                const hasResult = result?.document_id === doc.id

                return (
                  <div
                    key={doc.id}
                    className={`group relative overflow-hidden rounded-[24px] border px-5 py-4 transition-all ${
                      isCurrent
                        ? 'border-[#f5c26b]/25 bg-[#f5c26b]/5'
                        : 'border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]'
                    }`}
                  >
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      {/* Doc info */}
                      <div className="flex items-start gap-4">
                        <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border text-xl ${
                          isCurrent
                            ? 'border-[#f5c26b]/25 bg-[#f5c26b]/10'
                            : 'border-white/10 bg-white/[0.03]'
                        }`}>
                          <DocTypeIcon type={doc.document_type || doc.filename} />
                        </div>
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="truncate font-medium text-white">{doc.filename}</p>
                            {isCurrent && (
                              <span className="rounded-full bg-[#f5c26b]/15 px-2 py-0.5 text-[11px] text-[#f5c26b]">
                                Current
                              </span>
                            )}
                          </div>
                          <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-slate-500">
                            {doc.document_type && (
                              <span className="rounded-full border border-white/10 bg-white/[0.03] px-2 py-0.5">
                                {doc.document_type}
                              </span>
                            )}
                            <span>{formatSize(doc.file_size)}</span>
                            <span>{formatDate(doc.uploaded_at)}</span>
                          </div>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex flex-wrap items-center gap-2 sm:shrink-0">
                        {hasResult && (
                          <button
                            onClick={() => {
                              dispatch(setCurrentDocument(doc))
                              trackEvent('document_history_view_analysis', { documentId: doc.id })
                              navigate(`/analysis/${doc.id}`)
                            }}
                            className="rounded-xl border border-[#f5c26b]/20 bg-[#f5c26b]/8 px-4 py-2 text-xs font-medium text-[#f5c26b] transition hover:bg-[#f5c26b]/15"
                          >
                            View Analysis
                          </button>
                        )}
                        {hasResult && (
                          <button
                            onClick={() => {
                              dispatch(setCurrentDocument(doc))
                              trackEvent('document_history_open_chat', { documentId: doc.id })
                              navigate('/chat')
                            }}
                            className="rounded-xl border border-[#8a5cff]/20 bg-[#8a5cff]/8 px-4 py-2 text-xs font-medium text-[#c5b4ff] transition hover:bg-[#8a5cff]/15"
                          >
                            Ask AI
                          </button>
                        )}
                        {!hasResult && (
                          <button
                            onClick={() => handleReAnalyze(doc)}
                            disabled={isLoading}
                            className="rounded-xl border border-white/15 bg-white/[0.04] px-4 py-2 text-xs text-slate-300 transition hover:border-white/25 hover:text-white disabled:opacity-50"
                          >
                            {isLoading ? 'Analyzing...' : 'Re-analyze'}
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Risk summary for current doc */}
                    {hasResult && result && (
                      <div className="mt-3 flex flex-wrap gap-3 border-t border-white/8 pt-3">
                        <div className="flex items-center gap-1.5 text-xs">
                          <span className="h-2 w-2 rounded-full bg-[#fb7185]" />
                          <span className="text-slate-400">{result.summary.high_risk_count} high risk</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-xs">
                          <span className="h-2 w-2 rounded-full bg-[#f5c26b]" />
                          <span className="text-slate-400">{result.summary.medium_risk_count} medium risk</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-xs">
                          <span className="h-2 w-2 rounded-full bg-[#34d399]" />
                          <span className="text-slate-400">{result.summary.low_risk_count} low risk</span>
                        </div>
                        <span className="ml-auto text-xs text-slate-500">
                          Overall: <span className={
                            result.summary.overall_risk === 'high'
                              ? 'text-[#fb7185]'
                              : result.summary.overall_risk === 'medium'
                              ? 'text-[#f5c26b]'
                              : 'text-[#34d399]'
                          }>{result.summary.overall_risk} risk</span>
                        </span>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Quick tips for logged-out users */}
        {!user && (
          <div className="mt-6 section-card rounded-[32px] p-5 sm:p-7">
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-[#f5c26b]/20 bg-[#f5c26b]/8 text-sm text-[#f5c26b]">
                ℹ
              </div>
              <div>
                <p className="font-medium text-white">Sign in to persist your documents</p>
                <p className="mt-1 text-sm leading-6 text-slate-400">
                  Currently showing documents from this browser session only. Create an account to save your history permanently and access it from any device.
                </p>
                <div className="mt-3 flex gap-3">
                  <Link to="/register" className="btn-primary px-4 py-2 text-sm">Create Account</Link>
                  <Link to="/login" className="btn-secondary px-4 py-2 text-sm">Sign In</Link>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
