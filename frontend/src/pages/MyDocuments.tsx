import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { clearDocument, setCurrentDocument, fetchDocumentHistory, deleteDocuments } from '../store/documentSlice'
import type { UploadedDocument } from '../types'
import { trackEvent } from '../utils/posthog'
import { Card } from '../components/Card'
import { Modal } from '../components/ui/Modal'
import { documentDownloadUrl } from '../services/api'
import { enumLabel, formatBytes, formatDateTime, localizeKnownError } from '../utils/i18nHelpers'

function DocTypeIcon({ type }: { type: string }) {
  const t = type.toLowerCase()
  if (t.includes('rent') || t.includes('lease')) return <span>🏠</span>
  if (t.includes('employ') || t.includes('work')) return <span>💼</span>
  if (t.includes('loan') || t.includes('borrow')) return <span>🏦</span>
  if (t.includes('service') || t.includes('contract')) return <span>📋</span>
  return <span>📄</span>
}

/** Checkbox styled with the platform gold accent (gold fill + dark tick when checked). */
function ThemedCheckbox({
  checked,
  onChange,
  ariaLabel,
  className,
}: {
  checked: boolean
  onChange: () => void
  ariaLabel?: string
  className?: string
}) {
  return (
    <label className={`relative inline-flex h-[18px] w-[18px] cursor-pointer items-center justify-center ${className ?? ''}`}>
      <input type="checkbox" checked={checked} onChange={onChange} aria-label={ariaLabel} className="peer sr-only" />
      <span className="h-[18px] w-[18px] rounded-[6px] border border-white/25 bg-white/[0.06] transition-colors peer-hover:border-white/40 peer-checked:border-[#f5c26b] peer-checked:bg-[#f5c26b]" />
      <svg
        viewBox="0 0 12 12"
        fill="none"
        className="pointer-events-none absolute h-3 w-3 text-slate-950 opacity-0 transition-opacity peer-checked:opacity-100"
      >
        <path d="M2.5 6.2 4.7 8.4 9.5 3.6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </label>
  )
}

/** Trash / delete icon. */
function TrashIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <path d="M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2m2 0v12a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V7m4 4v6m4-6v6"
        stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export default function MyDocuments() {
  const { t, i18n } = useTranslation('documents')
  const formatSize = (bytes: number) => formatBytes(bytes, t, i18n.language)
  const formatDate = (iso: string) => formatDateTime(iso, i18n.language)
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { history, current } = useAppSelector((s) => s.document)
  const { result } = useAppSelector((s) => s.analysis)
  const { user, isAuthenticated, sessionChecked } = useAppSelector((s) => s.auth)

  const [selectionMode, setSelectionMode] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  function exitSelection() {
    setSelectionMode(false)
    setSelected(new Set())
  }

  // Redirect to login if not authenticated
  useEffect(() => {
    if (sessionChecked && !isAuthenticated) {
      navigate('/login')
    }
  }, [sessionChecked, isAuthenticated, navigate])

  // Load the persisted history (with per-document `analyzed` flags) on entry.
  useEffect(() => {
    if (isAuthenticated) dispatch(fetchDocumentHistory())
  }, [isAuthenticated, dispatch])

  // Drop any selected ids that no longer exist (e.g. after a delete).
  useEffect(() => {
    setSelected((prev) => {
      const ids = new Set(history.map((d) => d.id))
      const next = new Set([...prev].filter((id) => ids.has(id)))
      return next.size === prev.size ? prev : next
    })
  }, [history])

  const allSelected = history.length > 0 && selected.size === history.length

  const selectedDocs = useMemo(
    () => history.filter((d) => selected.has(d.id)),
    [history, selected]
  )

  function isAnalyzed(doc: UploadedDocument): boolean {
    return Boolean(doc.analyzed) || result?.document_id === doc.id
  }

  function toggleOne(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleAll() {
    setSelected((prev) => (prev.size === history.length ? new Set() : new Set(history.map((d) => d.id))))
  }

  function openAnalysis(doc: UploadedDocument) {
    // The analysis page loads the SAVED analysis (no re-analyze); if the document has
    // never been analysed it is analysed once there and then cached for next time.
    dispatch(setCurrentDocument(doc))
    trackEvent('document_history_view_analysis', { documentId: doc.id })
    navigate(`/analysis/${doc.id}`)
  }

  async function confirmDelete() {
    const ids = [...selected]
    if (ids.length === 0) return
    setDeleting(true)
    setDeleteError(null)
    try {
      await dispatch(deleteDocuments(ids)).unwrap()
      trackEvent('documents_deleted', { count: ids.length })
      setConfirmOpen(false)
      exitSelection()
    } catch (err) {
      setDeleteError(typeof err === 'string' ? localizeKnownError(t, err) : t('docerrors:delete'))
    } finally {
      setDeleting(false)
    }
  }

  function handleClearAndUpload() {
    dispatch(clearDocument())
    navigate('/upload')
  }

  if (!isAuthenticated) return null

  return (
    <div className="content-wrap py-5 sm:py-6">
      <div className="mx-auto max-w-7xl">

        {/* Header Container Card */}
        <Card variant="section" className="rounded-[32px] p-6 sm:p-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <span className="section-eyebrow">{t('eyebrow')}</span>
              <h1 className="mt-4 text-3xl font-semibold text-white sm:text-4xl">{t('title')}</h1>
              <p className="mt-2 text-sm leading-7 text-slate-400">
                {user ? t('signedInAs', { name: user.name, email: user.email }) : t('subtitleGuest')}
              </p>
            </div>
            <button onClick={handleClearAndUpload} className="btn-primary px-5 py-3">
              {t('uploadNew')}
            </button>
          </div>

          {/* Stats bar */}
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <Card variant="metric" className="rounded-[22px] px-5 py-4">
              <p className="text-3xl font-semibold text-white">{history.length}</p>
              <p className="mt-1 text-sm text-slate-400">{t('stats.saved')}</p>
            </Card>
            <Card variant="metric" className="rounded-[22px] px-5 py-4">
              <p className="text-3xl font-semibold text-[#f5c26b]">
                {result ? result.summary.high_risk_count : '—'}
              </p>
              <p className="mt-1 text-sm text-slate-400">{t('stats.highRisk')}</p>
            </Card>
            <Card variant="metric" className="rounded-[22px] px-5 py-4">
              <p className="text-3xl font-semibold text-[#34d399]">
                {result ? result.summary.total_clauses : '—'}
              </p>
              <p className="mt-1 text-sm text-slate-400">{t('stats.clauses')}</p>
            </Card>
          </div>
        </Card>

        {/* Document list Card */}
        <Card variant="section" className="mt-6 rounded-[32px] p-5 sm:p-7">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-xl font-semibold text-white">{t('recent')}</h2>

            {history.length > 0 && !selectionMode && (
              <button
                onClick={() => setSelectionMode(true)}
                aria-label={t('deleteAria')}
                title={t('deleteTitle')}
                className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-slate-300 transition hover:border-[#fb7185]/30 hover:text-[#fb7185]"
              >
                <TrashIcon className="h-4 w-4" />
                <span className="hidden sm:inline">{t('delete')}</span>
              </button>
            )}

            {history.length > 0 && selectionMode && (
              <div className="flex items-center gap-3">
                <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
                  <ThemedCheckbox checked={allSelected} onChange={toggleAll} ariaLabel={t('selectAllAria')} />
                  {t('selectAll')}
                </label>
                {selected.size > 0 && (
                  <span className="text-sm text-slate-500">{t('selectedCount', { count: selected.size })}</span>
                )}
                <button
                  onClick={() => setConfirmOpen(true)}
                  disabled={selected.size === 0}
                  className="flex items-center gap-1.5 rounded-xl border border-[#fb7185]/25 bg-[#fb7185]/8 px-4 py-2 text-xs font-medium text-[#fb7185] transition hover:bg-[#fb7185]/15 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <TrashIcon className="h-3.5 w-3.5" />
                  {selected.size > 0 ? t('deleteCount', { count: selected.size }) : t('delete')}
                </button>
                <button
                  onClick={exitSelection}
                  className="rounded-xl border border-white/15 bg-white/[0.04] px-4 py-2 text-xs font-medium text-slate-300 transition hover:border-white/25 hover:text-white"
                >
                  {t('cancel')}
                </button>
              </div>
            )}
          </div>

          {history.length === 0 ? (
            /* Empty state */
            <div className="flex flex-col items-center gap-5 py-16 text-center">
              <div className="flex h-24 w-24 items-center justify-center rounded-[30px] border border-white/10 bg-white/[0.03] text-4xl">
                📂
              </div>
              <div>
                <h3 className="text-xl font-semibold text-white">{t('empty.title')}</h3>
                <p className="mt-2 max-w-sm text-sm leading-7 text-slate-400">
                  {t('empty.body')}
                </p>
              </div>
              <Link to="/upload" className="btn-primary px-6 py-3">
                {t('empty.cta')}
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {history.map((doc) => {
                const isCurrent = doc.id === current?.id
                const analyzed = isAnalyzed(doc)
                const isSelected = selected.has(doc.id)
                const showSummary = result?.document_id === doc.id && result

                return (
                  <Card
                    key={doc.id}
                    variant="outline"
                    hoverLift
                    className={`relative overflow-hidden rounded-[24px] px-5 py-4 ${
                      isSelected ? 'border-[#fb7185]/30 bg-[#fb7185]/5' : isCurrent ? 'border-[#f5c26b]/25 bg-[#f5c26b]/5' : ''
                    }`}
                  >
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      {/* Doc info */}
                      <div className="flex items-start gap-3">
                        {selectionMode && (
                          <ThemedCheckbox
                            checked={isSelected}
                            onChange={() => toggleOne(doc.id)}
                            ariaLabel={t('selectOneAria', { name: doc.filename })}
                            className="mt-3.5 shrink-0"
                          />
                        )}
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
                                {t('badge.current')}
                              </span>
                            )}
                            {analyzed ? (
                              <span className="rounded-full bg-[#34d399]/15 px-2 py-0.5 text-[11px] text-[#34d399]">
                                {t('badge.analyzed')}
                              </span>
                            ) : (
                              <span className="rounded-full bg-white/10 px-2 py-0.5 text-[11px] text-slate-400">
                                {t('badge.notAnalyzed')}
                              </span>
                            )}
                          </div>
                          <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-slate-500">
                            {doc.document_type && (
                              <span className="rounded-full border border-white/10 bg-white/[0.03] px-2 py-0.5">
                                {enumLabel(t, 'clauses:docTypes', doc.document_type)}
                              </span>
                            )}
                            <span>{formatSize(doc.file_size)}</span>
                            <span>{formatDate(doc.uploaded_at)}</span>
                          </div>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex flex-wrap items-center gap-2 sm:shrink-0">
                        <button
                          onClick={() => openAnalysis(doc)}
                          className="rounded-xl border border-[#f5c26b]/20 bg-[#f5c26b]/8 px-4 py-2 text-xs font-medium text-[#f5c26b] transition hover:bg-[#f5c26b]/15"
                        >
                          {analyzed ? t('actions.showAnalysis') : t('actions.analyze')}
                        </button>
                        <a
                          href={documentDownloadUrl(doc.id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          aria-label={t('actions.downloadAria', { name: doc.filename })}
                          className="rounded-xl border border-white/15 bg-white/[0.04] px-4 py-2 text-xs font-medium text-slate-300 transition hover:border-white/25 hover:text-white"
                        >
                          {t('actions.download')}
                        </a>
                        {analyzed && (
                          <button
                            onClick={() => {
                              dispatch(setCurrentDocument(doc))
                              trackEvent('document_history_open_chat', { documentId: doc.id })
                              navigate('/chat')
                            }}
                            className="rounded-xl border border-[#8a5cff]/20 bg-[#8a5cff]/8 px-4 py-2 text-xs font-medium text-[#c5b4ff] transition hover:bg-[#8a5cff]/15"
                          >
                            {t('actions.askAi')}
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Risk summary for the currently loaded analysis */}
                    {showSummary && (
                      <div className="mt-3 flex flex-wrap gap-3 border-t border-white/8 pt-3">
                        <div className="flex items-center gap-1.5 text-xs">
                          <span className="h-2 w-2 rounded-full bg-[#fb7185]" />
                          <span className="text-slate-400">{t('summary.high', { count: result.summary.high_risk_count })}</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-xs">
                          <span className="h-2 w-2 rounded-full bg-[#f5c26b]" />
                          <span className="text-slate-400">{t('summary.medium', { count: result.summary.medium_risk_count })}</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-xs">
                          <span className="h-2 w-2 rounded-full bg-[#34d399]" />
                          <span className="text-slate-400">{t('summary.low', { count: result.summary.low_risk_count })}</span>
                        </div>
                        <span className="ml-auto text-xs text-slate-500">
                          {t('summary.overall')} <span className={
                            result.summary.overall_risk === 'high'
                              ? 'text-[#fb7185]'
                              : result.summary.overall_risk === 'medium'
                              ? 'text-[#f5c26b]'
                              : 'text-[#34d399]'
                          }>{t(`clauses:risk.${result.summary.overall_risk}`, { defaultValue: String(result.summary.overall_risk) })}</span>
                        </span>
                      </div>
                    )}
                  </Card>
                )
              })}
            </div>
          )}
        </Card>

        {/* Quick tips for logged-out users */}
        {!user && (
          <Card variant="section" className="mt-6 rounded-[32px] p-5 sm:p-7">
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-[#f5c26b]/20 bg-[#f5c26b]/8 text-sm text-[#f5c26b]">
                ℹ
              </div>
              <div>
                <p className="font-medium text-white">{t('guest.title')}</p>
                <p className="mt-1 text-sm leading-6 text-slate-400">
                  {t('guest.body')}
                </p>
                <div className="mt-3 flex gap-3">
                  <Link to="/register" className="btn-primary px-4 py-2 text-sm">{t('guest.createAccount')}</Link>
                  <Link to="/login" className="btn-secondary px-4 py-2 text-sm">{t('guest.signIn')}</Link>
                </div>
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* Delete confirmation dialog */}
      <Modal
        isOpen={confirmOpen}
        onClose={() => !deleting && setConfirmOpen(false)}
        closeOnBackdrop={!deleting}
        labelledBy="delete-dialog-title"
        look="card"
        size="sm"
        hideClose
      >
      <div className="flex items-start gap-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-[#fb7185]/25 bg-[#fb7185]/10 text-lg text-[#fb7185]" aria-hidden="true">
          🗑
        </div>
        <div className="min-w-0">
          <h3 id="delete-dialog-title" className="text-lg font-semibold text-white">
            {t('dialog.title', { count: selected.size })}
          </h3>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            {t('dialog.body', { count: selected.size })}
          </p>
          {selectedDocs.length > 0 && (
            <ul className="mt-3 max-h-28 space-y-1 overflow-y-auto text-xs text-slate-500">
              {selectedDocs.map((d) => (
                <li key={d.id} className="truncate">• {d.filename}</li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {deleteError && (
        <p role="alert" className="mt-4 rounded-lg border border-[#fb7185]/20 bg-[#fb7185]/10 px-3 py-2 text-xs text-[#fb7185]">
          {deleteError}
        </p>
      )}

      <div className="mt-6 flex justify-end gap-3">
        <button
          autoFocus
          onClick={() => setConfirmOpen(false)}
          disabled={deleting}
          className="rounded-xl border border-white/15 bg-white/[0.04] px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-white/25 disabled:opacity-50"
        >
          {t('dialog.cancel')}
        </button>
        <button
          onClick={confirmDelete}
          disabled={deleting}
          className="rounded-xl bg-[#fb7185] px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-[#fca5b5] disabled:opacity-60"
        >
          {deleting ? t('dialog.deleting') : t('dialog.confirm')}
        </button>
      </div>
      </Modal>
    </div>
  )
}
