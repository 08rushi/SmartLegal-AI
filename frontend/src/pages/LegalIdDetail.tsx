import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import {
  fetchIdGuidance,
  fetchApplications,
  createApplication,
  fetchChecklist,
  saveChecklist,
} from '../store/legalIdSlice'
import type { LegalIdGuidance, ChecklistItem } from '../types'
import ServiceArt from '../components/ServiceArt'

export default function LegalIdDetail() {
  const { idType } = useParams<{ idType: string }>()
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { currentGuidance, applications, currentChecklist, isLoading, error } = useAppSelector(
    (state) => state.legalId
  )
  const { token } = useAppSelector((state) => state.auth)

  const [activeTab, setActiveTab] = useState<'services' | 'checklist' | 'faqs' | 'rights'>(
    'services'
  )
  const [showTrackerModal, setShowTrackerModal] = useState(false)
  const [selectedService, setSelectedService] = useState('')
  const [trackerStatus, setTrackerStatus] = useState('in_progress')
  const [trackerNotes, setTrackerNotes] = useState('')
  const [trackerLoading, setTrackerLoading] = useState(false)
  const [checklistItems, setChecklistItems] = useState<ChecklistItem[]>([])
  const [currentAppId, setCurrentAppId] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted || !idType) return
    dispatch(fetchIdGuidance(idType))
    if (token) {
      dispatch(fetchApplications())
    }
  }, [mounted, dispatch, idType, token])

  // Sync Redux checklist state to local state
  useEffect(() => {
    setChecklistItems(currentChecklist)
  }, [currentChecklist])

  const userAppsForThisId = applications.filter((app) => app.id_type === idType)

  const handleCreateApplication = async () => {
    if (!selectedService) return
    setTrackerLoading(true)
    try {
      const resultAction = await dispatch(
        createApplication({
          id_type: idType!,
          service: selectedService,
          notes: trackerNotes,
        })
      )
      if (createApplication.fulfilled.match(resultAction)) {
        setShowTrackerModal(false)
        setSelectedService('')
        setTrackerNotes('')
        setTrackerStatus('in_progress')
      }
    } finally {
      setTrackerLoading(false)
    }
  }

  const handleViewChecklist = async (appId: string) => {
    setCurrentAppId(appId)
    setActiveTab('checklist')
    const resultAction = await dispatch(fetchChecklist(appId))
    if (fetchChecklist.rejected.match(resultAction)) {
      alert(`Failed to load checklist: ${resultAction.payload}`)
    }
  }

  const handleToggleChecklistItem = (item: ChecklistItem) => {
    const updated = checklistItems.map((i) =>
      i.id === item.id ? { ...i, is_done: !i.is_done } : i
    )
    setChecklistItems(updated)
  }

  const handleSaveChecklist = async () => {
    if (!currentAppId) return
    setTrackerLoading(true)
    try {
      const resultAction = await dispatch(
        saveChecklist({
          app_id: currentAppId,
          items: checklistItems.map((i) => ({
            id: i.id,
            item_text: i.item_text,
            is_done: i.is_done,
          })),
        })
      )
      if (saveChecklist.fulfilled.match(resultAction)) {
        // Show success message
        alert('Checklist saved successfully')
      } else if (saveChecklist.rejected.match(resultAction)) {
        // Show error message
        alert(`Failed to save checklist: ${resultAction.payload}`)
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
            <p className="mt-4 text-white/40">Loading details...</p>
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
            onClick={() => navigate('/legal-id')}
            className="inline-block text-blue-400 hover:text-blue-300 mb-6 text-sm font-medium"
          >
            ← Back to Hub
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
            onClick={() => navigate('/legal-id')}
            className="inline-block text-blue-400 hover:text-blue-300 mb-6 text-sm font-medium"
          >
            ← Back to Hub
          </button>
          <p className="text-white/60">ID type not found.</p>
        </div>
      </div>
    )
  }

  const guidance: LegalIdGuidance = currentGuidance

  return (
    <div className="content-wrap py-5 sm:py-6">
      <div className="section-card mx-auto max-w-7xl rounded-[32px] p-6 sm:p-8">
        {/* ─ Back Button ─ */}
        <button
          onClick={() => navigate('/legal-id')}
          className="inline-block text-blue-400 hover:text-blue-300 transition-colors text-sm font-medium mb-6"
        >
          ← Back to Legal ID Hub
        </button>

        {/* ─ Main Layout: Sidebar + Content ─ */}
        <div className="xl:grid xl:grid-cols-[260px_minmax(0,1fr)] gap-8">
        {/* ─ Sidebar ─ */}
        <div className="space-y-6 mb-12 xl:mb-0">
          {/* ID Info Card */}
          <div className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6">
            <div className="mb-4 h-28 overflow-hidden rounded-xl border border-white/10 bg-white/[0.02]">
              <ServiceArt hub="legal-id" serviceKey={idType || ''} preserve="xMidYMid meet" />
            </div>
            <h1 className="text-2xl font-bold text-white">{guidance.display_name}</h1>
            <p className="text-sm text-white/60 mt-2">{guidance.authority}</p>
            <a
              href={guidance.official_portal}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block text-xs text-blue-400 hover:text-blue-300 mt-4 underline"
            >
              Official Portal →
            </a>
          </div>

          {/* My Applications for This ID */}
          {token && (
            <div className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6">
              <h3 className="font-semibold text-white mb-4">My Applications</h3>
              {userAppsForThisId.length === 0 ? (
                <p className="text-sm text-white/50 mb-4">No applications yet.</p>
              ) : (
                <div className="space-y-3 mb-4">
                  {userAppsForThisId.map((app) => {
                    const statusColors = {
                      in_progress: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400',
                      submitted: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
                      received: 'bg-green-500/10 border-green-500/20 text-green-400',
                      completed: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
                    }
                    const statusBgColor = statusColors[app.status as keyof typeof statusColors]

                    return (
                      <div
                        key={app.id}
                        className="rounded border border-white/10 bg-white/[0.03] p-3"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <p className="text-sm font-medium text-white">{app.service}</p>
                        </div>
                        <div className={`inline-block rounded px-2 py-1 text-xs font-medium border ${statusBgColor}`}>
                          {app.status.replace('_', ' ').charAt(0).toUpperCase() +
                            app.status.replace('_', ' ').slice(1)}
                        </div>
                        <button
                          onClick={() => handleViewChecklist(app.id)}
                          className="text-xs text-blue-400 hover:text-blue-300 mt-3 block"
                        >
                          View Checklist →
                        </button>
                      </div>
                    )
                  })}
                </div>
              )}

              {token && (
                <button
                  onClick={() => setShowTrackerModal(true)}
                  className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
                >
                  Track New Application
                </button>
              )}
            </div>
          )}

          {/* CTA for Non-Logged-In Users */}
          {!token && (
            <div className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6">
              <p className="text-sm text-white/60 mb-4">
                Sign in to track your application progress and save checklists.
              </p>
              <button
                onClick={() => navigate('/login')}
                className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
              >
                Sign In
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
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
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
                    {service.description && (
                      <p className="text-sm text-white/60 ml-4">{service.description}</p>
                    )}
                  </div>

                  <div className="space-y-3">
                    <div>
                      <p className="text-xs font-medium text-white/40 uppercase tracking-wide">Where</p>
                      <p className="text-sm text-white/80 mt-1">{service.where}</p>
                    </div>

                    <div>
                      <p className="text-xs font-medium text-white/40 uppercase tracking-wide">
                        Documents Required
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
                        <p className="text-xs font-medium text-white/40 uppercase tracking-wide">Fee</p>
                        <p className="text-sm text-white/80 mt-1">{service.fee}</p>
                      </div>
                      <div>
                        <p className="text-xs font-medium text-white/40 uppercase tracking-wide">Timeline</p>
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
                        View Official Details →
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
              {!token ? (
                <div className="text-center py-12">
                  <p className="text-white/60 mb-6">Sign in to view and manage your checklist.</p>
                  <button
                    onClick={() => navigate('/login')}
                    className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
                  >
                    Sign In
                  </button>
                </div>
              ) : currentAppId && checklistItems.length > 0 ? (
                <div className="space-y-4">
                  <div className="space-y-2">
                    {checklistItems.map((item) => (
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
                    ))}
                  </div>

                  <button
                    onClick={handleSaveChecklist}
                    disabled={trackerLoading}
                    className="mt-6 rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {trackerLoading ? 'Saving...' : 'Save Checklist'}
                  </button>
                </div>
              ) : (
                <div className="text-center py-12">
                  <p className="text-white/60">
                    Select an application or create a new one to view its checklist.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* ─ FAQs Tab ─ */}
          {activeTab === 'faqs' && (
            <div className="space-y-4">
              {guidance.faqs.map((faq, idx) => (
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
              ))}
            </div>
          )}

          {/* ─ Legal Rights Tab ─ */}
          {activeTab === 'rights' && (
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
          )}
        </div>
      </div>

        {/* ─ Disclaimer Banner ─ */}
        <div className="mt-8 rounded-2xl border border-white/10 bg-white/[0.02] p-5">
          <p className="text-sm text-white/60">{guidance.disclaimer}</p>
        </div>
      </div>

      {/* ─ Tracker Modal ─ */}
      {showTrackerModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="rounded-lg border border-white/10 bg-slate-800 backdrop-blur-sm max-w-md w-full p-8 space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white">Track New Application</h2>
              <p className="text-white/60 mt-2">Create a new application tracker for {guidance.display_name}</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">Select Service</label>
                <select
                  value={selectedService}
                  onChange={(e) => setSelectedService(e.target.value)}
                  className="w-full rounded-lg border border-white/20 bg-white/5 text-white px-4 py-2 text-sm"
                >
                  <option value="">Choose a service...</option>
                  {guidance.services.map((svc) => (
                    <option key={svc.service} value={svc.service}>
                      {svc.service}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-2">Application Status</label>
                <div className="grid grid-cols-2 gap-2">
                  {(['in_progress', 'submitted', 'received', 'completed'] as const).map((status) => {
                    const statusColors = {
                      in_progress: 'bg-yellow-500/10 border-yellow-500/20',
                      submitted: 'bg-blue-500/10 border-blue-500/20',
                      received: 'bg-green-500/10 border-green-500/20',
                      completed: 'bg-amber-500/10 border-amber-500/20',
                    }
                    return (
                      <button
                        key={status}
                        onClick={() => setTrackerStatus(status)}
                        className={`rounded-lg border px-3 py-2 text-sm font-medium transition-all ${
                          trackerStatus === status
                            ? `${statusColors[status]} border-current ring-2 ring-offset-2 ring-offset-slate-800`
                            : 'border-white/10 text-white/60 hover:text-white'
                        }`}
                      >
                        {status.replace('_', ' ').charAt(0).toUpperCase() +
                          status.replace('_', ' ').slice(1)}
                      </button>
                    )
                  })}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-2">Notes (Optional)</label>
                <textarea
                  value={trackerNotes}
                  onChange={(e) => setTrackerNotes(e.target.value)}
                  placeholder="Add any notes about your application..."
                  className="w-full rounded-lg border border-white/20 bg-white/5 text-white px-4 py-3 text-sm placeholder-white/30 resize-none h-24"
                />
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <button
                onClick={() => setShowTrackerModal(false)}
                className="flex-1 rounded-lg border border-white/20 px-4 py-2 text-sm font-medium text-white hover:bg-white/5 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateApplication}
                disabled={!selectedService || trackerLoading}
                className="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {trackerLoading ? 'Creating...' : 'Create Application'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
