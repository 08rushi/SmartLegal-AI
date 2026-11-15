import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { HUB_ADAPTERS, HUB_BASE_PATH, HUB_STATUSES, type HubId } from './hubs/hubAdapters'
import type { ChecklistItem } from '../types'
import ServiceArt from './ServiceArt'
import { Modal } from './ui/Modal'

/**
 * Detail page shared by Legal ID, Property and Business (the pages are thin wrappers).
 * Markup follows the original three pages; `legal` switches the few places where the Legal ID page differed.
 * TODO(i18n-content): service names, documents, fees, FAQs and legal text come from the backend (?lang=).
 */

interface HubService {
  service: string
  description?: string
  where: string
  documents_required: string[]
  fee: string
  timeline: string
  official_link: string
}

export interface HubGuidance {
  display_name: string
  authority: string
  official_portal: string
  services: HubService[]
  faqs: { q: string; a: string }[]
  common_issues?: string[]
  legal_protections: string[]
  disclaimer: string
}

type Tab = 'services' | 'checklist' | 'faqs' | 'rights'

const statusColors: Record<string, string> = {
  in_progress: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400',
  submitted: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
  received: 'bg-green-500/10 border-green-500/20 text-green-400',
  completed: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
}

const statusPickColors: Record<string, string> = {
  in_progress: 'bg-yellow-500/10 border-yellow-500/20',
  submitted: 'bg-blue-500/10 border-blue-500/20',
  received: 'bg-green-500/10 border-green-500/20',
  completed: 'bg-amber-500/10 border-amber-500/20',
}

export default function HubDetailView({ hub, typeKey }: { hub: HubId; typeKey: string }) {
  const adapter = HUB_ADAPTERS[hub]
  const legal = hub === 'legal-id'
  const { t, i18n } = useTranslation('hubs')
  const { t: th } = useTranslation(adapter.ns)
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const snap = useAppSelector(adapter.select)
  const { isAuthenticated } = useAppSelector((state) => state.auth)
  const { isLoading, error } = snap
  const currentGuidance = snap.guidance
  const backPath = HUB_BASE_PATH[hub]

  const [activeTab, setActiveTab] = useState<Tab>('services')
  const [showTrackerModal, setShowTrackerModal] = useState(false)
  const [selectedService, setSelectedService] = useState('')
  const [trackerStatus, setTrackerStatus] = useState('in_progress')
  const [trackerNotes, setTrackerNotes] = useState('')
  const [trackerLoading, setTrackerLoading] = useState(false)
  const [checklistItems, setChecklistItems] = useState<ChecklistItem[]>([])
  const [currentAppId, setCurrentAppId] = useState<string | null>(null)
  /** Statuses shown immediately while their PATCH is in flight (dropped again on failure). */
  const [pendingStatus, setPendingStatus] = useState<Record<string, string>>({})

  // Refetch on language change: guidance text and server errors come back in the active language (?lang=).
  useEffect(() => {
    if (!typeKey) return
    adapter.fetchGuidance(dispatch, typeKey)
    if (isAuthenticated) adapter.fetchApps(dispatch)
  }, [adapter, dispatch, typeKey, isAuthenticated, i18n.language])

  // Sync Redux checklist state to local state
  useEffect(() => {
    setChecklistItems(snap.checklist)
  }, [snap.checklist])

  const userAppsForThisType = snap.apps.filter((app) => app.type === typeKey)

  const handleCreateApplication = async () => {
    if (!selectedService) return
    setTrackerLoading(true)
    try {
      const chosen = trackerStatus
      const newId = await adapter.create(dispatch, typeKey, selectedService, trackerNotes)
      if (newId) {
        setShowTrackerModal(false)
        setSelectedService('')
        setTrackerNotes('')
        setTrackerStatus('in_progress')
        // The create call has no status field: apply the chosen status with PATCH (optimistic, reverted on error).
        if (legal && chosen !== 'in_progress') {
          setPendingStatus((p) => ({ ...p, [newId]: chosen }))
          const res = await adapter.updateStatus(dispatch, newId, chosen)
          setPendingStatus((p) => {
            const { [newId]: _drop, ...rest } = p
            return rest
          })
          if (!res.ok) alert(t('detail.statusFailed'))
        }
      }
    } finally {
      setTrackerLoading(false)
    }
  }

  const handleViewChecklist = async (appId: string) => {
    setCurrentAppId(appId)
    setActiveTab('checklist')
    const res = await adapter.fetchChecklist(dispatch, appId)
    if (!res.ok) {
      alert(t('detail.checklist.loadFailed', { error: res.error ?? '' }))
    }
  }

  const handleToggleChecklistItem = (item: ChecklistItem) => {
    const updated = checklistItems.map((i) => (i.id === item.id ? { ...i, is_done: !i.is_done } : i))
    setChecklistItems(updated)
  }

  const handleSaveChecklist = async () => {
    if (!currentAppId) return
    setTrackerLoading(true)
    try {
      const res = await adapter.saveChecklist(dispatch, currentAppId, checklistItems)
      if (res.ok) {
        alert(t('detail.checklist.saved'))
      } else {
        alert(t('detail.checklist.saveFailed', { error: res.error ?? '' }))
      }
    } finally {
      setTrackerLoading(false)
    }
  }

  if (isLoading && !currentGuidance) {
    return (
      <div className="content-wrap py-5 sm:py-6">
        <div className="section-card mx-auto max-w-7xl rounded-[32px] p-6 sm:p-8">
          <div className="text-center py-16">
            <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin mx-auto" />
            <p className="mt-4 text-white/40">{t('detail.loading')}</p>
          </div>
        </div>
      </div>
    )
  }

  if (error && !currentGuidance) {
    return (
      <div className="content-wrap py-5 sm:py-6">
        <div className="section-card mx-auto max-w-7xl rounded-[32px] p-6 sm:p-8">
          <button
            onClick={() => navigate(backPath)}
            className="inline-block text-blue-400 hover:text-blue-300 mb-6 text-sm font-medium"
          >
            ← {t('detail.backShort')}
          </button>
          <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6">
            <p className="text-red-400">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (!currentGuidance) {
    return (
      <div className="content-wrap py-5 sm:py-6">
        <div className="section-card mx-auto max-w-7xl rounded-[32px] p-6 sm:p-8">
          <button
            onClick={() => navigate(backPath)}
            className="inline-block text-blue-400 hover:text-blue-300 mb-6 text-sm font-medium"
          >
            ← {t('detail.backShort')}
          </button>
          <p className="text-white/60">{th('notFound')}</p>
        </div>
      </div>
    )
  }

  const guidance: HubGuidance = currentGuidance
  const typeName = th(`types.${typeKey}`, { defaultValue: guidance.display_name })
  const statusText = (status: string) => t(`status.${status}`, { defaultValue: status.replace('_', ' ') })

  return (
    <div className="content-wrap py-5 sm:py-6">
      <div className="section-card mx-auto max-w-7xl rounded-[32px] p-6 sm:p-8">
        {/* ─ Back Button ─ */}
        <button
          onClick={() => navigate(backPath)}
          className="inline-block text-blue-400 hover:text-blue-300 transition-colors text-sm font-medium mb-6"
        >
          ← {th('backToHub')}
        </button>

        {/* ─ Main Layout: Sidebar + Content ─ */}
        <div className="xl:grid xl:grid-cols-[260px_minmax(0,1fr)] gap-8">
        {/* ─ Sidebar ─ */}
        <div className="space-y-6 mb-12 xl:mb-0">
          {/* Info Card */}
          <div className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6">
            <div className="mb-4 h-28 overflow-hidden rounded-xl border border-white/10 bg-white/[0.02]">
              <ServiceArt hub={hub} serviceKey={typeKey} preserve="xMidYMid meet" />
            </div>
            <h1 className="text-2xl font-bold text-white">{typeName}</h1>
            <p className="text-sm text-white/60 mt-2">{guidance.authority}</p>
            <a
              href={guidance.official_portal}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block text-xs text-blue-400 hover:text-blue-300 mt-4 underline"
            >
              {t('detail.officialPortal')}
            </a>
          </div>

          {/* My Applications for This Type */}
          {isAuthenticated && (
            <div className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6">
              <h3 className="font-semibold text-white mb-4">{t('detail.myApplications')}</h3>
              {userAppsForThisType.length === 0 ? (
                <p className="text-sm text-white/50 mb-4">{t('detail.noApplications')}</p>
              ) : (
                <div className="space-y-3 mb-4">
                  {userAppsForThisType.map((app) => {
                    const shown = pendingStatus[app.id] ?? app.status
                    const statusBgColor = statusColors[shown]

                    return (
                      <div
                        key={app.id}
                        className="rounded border border-white/10 bg-white/[0.03] p-3"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <p className="text-sm font-medium text-white">{app.service}</p>
                        </div>
                        <div className={`inline-block rounded px-2 py-1 text-xs font-medium border ${statusBgColor}`}>
                          {statusText(shown)}
                        </div>
                        <button
                          onClick={() => handleViewChecklist(app.id)}
                          className="text-xs text-blue-400 hover:text-blue-300 mt-3 block"
                        >
                          {t('detail.viewChecklist')}
                        </button>
                      </div>
                    )
                  })}
                </div>
              )}

              <button
                onClick={() => setShowTrackerModal(true)}
                className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
              >
                {t('detail.trackNew')}
              </button>
            </div>
          )}

          {/* CTA for Non-Logged-In Users */}
          {!isAuthenticated && (
            <div className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6">
              <p className="text-sm text-white/60 mb-4">
                {t('detail.signInPrompt')}
              </p>
              <button
                onClick={() => navigate('/login')}
                className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
              >
                {t('detail.signIn')}
              </button>
            </div>
          )}
        </div>

        {/* ─ Main Content ─ */}
        <div className="space-y-6">
          {/* ─ Tabs ─ */}
          <div className="flex gap-2 border-b border-white/10">
            {(['services', 'checklist', 'faqs', 'rights'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-4 px-2 font-medium text-sm transition-colors relative ${
                  activeTab === tab
                    ? 'text-white'
                    : 'text-white/50 hover:text-white/70'
                }`}
              >
                {t(`detail.tabs.${tab}`)}
                {activeTab === tab && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
                )}
              </button>
            ))}
          </div>

          {/* ─ Services Tab ─ */}
          {activeTab === 'services' && (
            <div className="space-y-4">
              {guidance.services.map((service, idx) => (
                <div
                  key={idx}
                  className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6"
                >
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white">{service.service}</h3>
                    {legal && service.description && (
                      <p className="text-sm text-white/60 ml-4">{service.description}</p>
                    )}
                  </div>

                  <div className="space-y-3">
                    {!legal && (
                      <div>
                        <p className="text-xs font-medium text-white/40 uppercase tracking-wide">{t('detail.description')}</p>
                        <p className="text-sm text-white/80 mt-1">{service.description}</p>
                      </div>
                    )}

                    <div>
                      <p className="text-xs font-medium text-white/40 uppercase tracking-wide">{t('detail.where')}</p>
                      <p className="text-sm text-white/80 mt-1">{service.where}</p>
                    </div>

                    <div>
                      <p className="text-xs font-medium text-white/40 uppercase tracking-wide">
                        {t('detail.documentsRequired')}
                      </p>
                      <ul className="mt-2 space-y-1">
                        {service.documents_required.map((doc, idx) => (
                          <li key={idx} className="text-sm text-white/80 flex gap-2">
                            <span className="text-blue-400">•</span> {doc}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs font-medium text-white/40 uppercase tracking-wide">{t('detail.fee')}</p>
                        <p className="text-sm text-white/80 mt-1">{service.fee}</p>
                      </div>
                      <div>
                        <p className="text-xs font-medium text-white/40 uppercase tracking-wide">{t('detail.timeline')}</p>
                        <p className="text-sm text-white/80 mt-1">{service.timeline}</p>
                      </div>
                    </div>

                    <div>
                      <a
                        href={service.official_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-400 hover:text-blue-300 underline"
                      >
                        {t('detail.officialDetails')}
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ─ Checklist Tab ─ */}
          {activeTab === 'checklist' && (
            <div className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6">
              {!isAuthenticated ? (
                legal ? (
                  <div className="text-center py-12">
                    <p className="text-white/60 mb-6">{t('detail.checklist.signIn')}</p>
                    <button
                      onClick={() => navigate('/login')}
                      className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
                    >
                      {t('detail.signIn')}
                    </button>
                  </div>
                ) : (
                  <p className="text-white/60 text-center py-8">{t('detail.checklist.signIn')}</p>
                )
              ) : currentAppId && (legal ? checklistItems.length > 0 : true) ? (
                <div className="space-y-4">
                  <div className={legal ? 'space-y-2' : 'space-y-3'}>
                    {checklistItems.map((item) =>
                      legal ? (
                        <label
                          key={item.id}
                          className="flex items-center gap-3 p-3 rounded-lg hover:bg-white/[0.05] transition-colors cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={item.is_done}
                            onChange={() => handleToggleChecklistItem(item)}
                            className="w-5 h-5 rounded border-white/20 text-blue-600 cursor-pointer"
                          />
                          <span
                            className={`text-sm ${
                              item.is_done
                                ? 'text-white/50 line-through'
                                : 'text-white'
                            }`}
                          >
                            {item.item_text}
                          </span>
                        </label>
                      ) : (
                        <label key={item.id} className="flex items-start gap-3 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={item.is_done}
                            onChange={() => handleToggleChecklistItem(item)}
                            className="mt-1"
                          />
                          <span className={`text-sm ${item.is_done ? 'text-white/50 line-through' : 'text-white/80'}`}>
                            {item.item_text}
                          </span>
                        </label>
                      ),
                    )}
                  </div>

                  <button
                    onClick={handleSaveChecklist}
                    disabled={trackerLoading}
                    className={
                      legal
                        ? 'mt-6 rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors'
                        : 'w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors disabled:bg-blue-600/50'
                    }
                  >
                    {trackerLoading ? t('detail.checklist.saving') : t('detail.checklist.save')}
                  </button>
                </div>
              ) : legal ? (
                <div className="text-center py-12">
                  <p className="text-white/60">
                    {t('detail.checklist.select')}
                  </p>
                </div>
              ) : (
                <p className="text-white/60 text-center py-8">{t('detail.checklist.select')}</p>
              )}
            </div>
          )}

          {/* ─ FAQs Tab ─ */}
          {activeTab === 'faqs' && (
            <div className="space-y-4">
              {guidance.faqs.map((faq, idx) =>
                legal ? (
                  <details
                    key={idx}
                    className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6 group cursor-pointer"
                  >
                    <summary className="font-semibold text-white flex items-center justify-between">
                      {faq.q}
                      <span className="ml-2 text-white/60 group-open:rotate-180 transition-transform">
                        ▼
                      </span>
                    </summary>
                    <p className="text-white/70 mt-4">{faq.a}</p>
                  </details>
                ) : (
                  <div
                    key={idx}
                    className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6"
                  >
                    <h3 className="text-lg font-semibold text-white mb-3">{faq.q}</h3>
                    <p className="text-white/80 text-sm">{faq.a}</p>
                  </div>
                ),
              )}
            </div>
          )}

          {/* ─ Legal Rights / Protections Tab ─ */}
          {activeTab === 'rights' &&
            (legal ? (
              <div className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6">
                <div className="space-y-3">
                  {guidance.legal_protections.map((protection, idx) => (
                    <div key={idx} className="flex gap-3">
                      <span className="text-blue-400 font-semibold">▪</span>
                      <p className="text-white/80">{protection}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">{t('detail.rights.protections')}</h3>
                  <ul className="space-y-3">
                    {guidance.legal_protections.map((protection, idx) => (
                      <li key={idx} className="text-sm text-white/80 flex gap-3">
                        <span className="text-blue-400 mt-1">→</span>
                        <span>{protection}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {guidance.common_issues && guidance.common_issues.length > 0 && (
                  <div className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">{t('detail.rights.commonIssues')}</h3>
                    <ul className="space-y-3">
                      {guidance.common_issues.map((issue, idx) => (
                        <li key={idx} className="text-sm text-white/80 flex gap-3">
                          <span className="text-yellow-400 mt-1">⚠</span>
                          <span>{issue}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6">
                  <h3 className="text-sm font-semibold text-red-400 mb-2">{t('detail.rights.disclaimer')}</h3>
                  <p className="text-xs text-red-400/80">{guidance.disclaimer}</p>
                </div>
              </div>
            ))}
        </div>
      </div>

        {/* ─ Disclaimer Banner ─ */}
        {legal && (
          <div className="mt-8 rounded-2xl border border-white/10 bg-white/[0.02] p-5">
            <p className="text-sm text-white/60">{guidance.disclaimer}</p>
          </div>
        )}
      </div>

      {/* ─ Tracker Modal (ui/Modal: focus trap, Escape, labelled dialog) ─ */}
      <Modal isOpen={showTrackerModal} onClose={() => setShowTrackerModal(false)} title={t('detail.modal.title')} size="sm">
        <div className="space-y-6">
          {legal && <p className="text-white/60">{t('detail.modal.intro', { name: typeName })}</p>}

          <div className="space-y-4">
            <div>
              <label htmlFor="hub-track-service" className="block text-sm font-medium text-white mb-2">{t('detail.modal.selectService')}</label>
              <select
                id="hub-track-service"
                value={selectedService}
                onChange={(e) => setSelectedService(e.target.value)}
                className="w-full rounded-lg border border-white/20 bg-white/5 text-white px-4 py-2 text-sm"
              >
                <option value="">{t('detail.modal.choose')}</option>
                {guidance.services.map((svc) => (
                  <option key={svc.service} value={svc.service}>
                    {svc.service}
                  </option>
                ))}
              </select>
            </div>

            {legal && (
              <div>
                <p className="block text-sm font-medium text-white mb-2">{t('detail.modal.status')}</p>
                <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-label={t('detail.modal.status')}>
                  {HUB_STATUSES.map((status) => (
                    <button
                      key={status}
                      type="button"
                      role="radio"
                      aria-checked={trackerStatus === status}
                      onClick={() => setTrackerStatus(status)}
                      className={`rounded-lg border px-3 py-2 text-sm font-medium transition-all ${
                        trackerStatus === status
                          ? `${statusPickColors[status]} border-current ring-2 ring-offset-2 ring-offset-slate-800`
                          : 'border-white/10 text-white/60 hover:text-white'
                      }`}
                    >
                      {statusText(status)}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div>
              <label htmlFor="hub-track-notes" className="block text-sm font-medium text-white mb-2">{t('detail.modal.notes')}</label>
              <textarea
                id="hub-track-notes"
                value={trackerNotes}
                onChange={(e) => setTrackerNotes(e.target.value)}
                placeholder={t('detail.modal.notesPlaceholder')}
                className="w-full rounded-lg border border-white/20 bg-white/5 text-white px-4 py-3 text-sm placeholder-white/30 resize-none h-24"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={() => setShowTrackerModal(false)}
              className="flex-1 rounded-lg border border-white/20 px-4 py-2 text-sm font-medium text-white hover:bg-white/5 transition-colors"
            >
              {t('detail.modal.cancel')}
            </button>
            <button
              type="button"
              onClick={handleCreateApplication}
              disabled={!selectedService || trackerLoading}
              className="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {trackerLoading ? t('detail.modal.creating') : t('detail.modal.create')}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
