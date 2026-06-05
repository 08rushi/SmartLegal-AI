import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import {
  fetchBusinessGuidance,
  fetchBusinessApplications,
  createApplication,
  fetchChecklist,
  saveBusinessChecklist,
} from '../store/businessSlice'
import type { BusinessGuidance, ChecklistItem } from '../types'

export default function BusinessDetail() {
  const { businessType } = useParams<{ businessType: string }>()
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { currentGuidance, applications, currentChecklist, isLoading, error } = useAppSelector(
    (state) => state.business
  )
  const { token } = useAppSelector((state) => state.auth)

  const [activeTab, setActiveTab] = useState<'services' | 'checklist' | 'faqs' | 'rights'>(
    'services'
  )
  const [showTrackerModal, setShowTrackerModal] = useState(false)
  const [selectedService, setSelectedService] = useState('')
  const [trackerNotes, setTrackerNotes] = useState('')
  const [trackerLoading, setTrackerLoading] = useState(false)
  const [checklistItems, setChecklistItems] = useState<ChecklistItem[]>([])
  const [currentAppId, setCurrentAppId] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted || !businessType) return
    dispatch(fetchBusinessGuidance(businessType))
    if (token) {
      dispatch(fetchBusinessApplications())
    }
  }, [mounted, dispatch, businessType, token])

  useEffect(() => {
    setChecklistItems(currentChecklist)
  }, [currentChecklist])

  const userAppsForThisBusiness = applications.filter((app) => app.business_type === businessType)

  const handleCreateApplication = async () => {
    if (!selectedService) return
    setTrackerLoading(true)
    try {
      const resultAction = await dispatch(
        createApplication({
          business_type: businessType!,
          service: selectedService,
          notes: trackerNotes,
        })
      )
      if (createApplication.fulfilled.match(resultAction)) {
        setShowTrackerModal(false)
        setSelectedService('')
        setTrackerNotes('')
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
        saveBusinessChecklist({
          app_id: currentAppId,
          items: checklistItems.map((i) => ({
            id: i.id,
            item_text: i.item_text,
            is_done: i.is_done,
          })),
        })
      )
      if (saveBusinessChecklist.fulfilled.match(resultAction)) {
        alert('Checklist saved successfully')
      } else if (saveBusinessChecklist.rejected.match(resultAction)) {
        alert(`Failed to save checklist: ${resultAction.payload}`)
      }
    } finally {
      setTrackerLoading(false)
    }
  }

  if (isLoading && !currentGuidance) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin mx-auto" />
          <p className="mt-4 text-white/40">Loading details...</p>
        </div>
      </div>
    )
  }

  if (error && !currentGuidance) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800">
        <div className="content-wrap py-12">
          <button
            onClick={() => navigate('/business-hub')}
            className="text-blue-400 hover:text-blue-300 mb-6"
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
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800">
        <div className="content-wrap py-12">
          <button
            onClick={() => navigate('/business-hub')}
            className="text-blue-400 hover:text-blue-300 mb-6"
          >
            ← Back to Hub
          </button>
          <p className="text-white/60">Business type not found.</p>
        </div>
      </div>
    )
  }

  const guidance: BusinessGuidance = currentGuidance

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800">
      {/* ─ Back Button ─ */}
      <div className="content-wrap border-b border-white/10 py-4">
        <button
          onClick={() => navigate('/business-hub')}
          className="text-blue-400 hover:text-blue-300 transition-colors text-sm font-medium"
        >
          ← Back to Business License Hub
        </button>
      </div>

      {/* ─ Main Layout: Sidebar + Content ─ */}
      <div className="xl:grid xl:grid-cols-[260px_minmax(0,1fr)] gap-8 content-wrap py-12">
        {/* ─ Sidebar ─ */}
        <div className="space-y-6 mb-12 xl:mb-0">
          {/* Business Info Card */}
          <div className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6">
            <div className="text-5xl mb-4">{guidance.icon}</div>
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

          {/* My Applications for This Business Type */}
          {token && (
            <div className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6">
              <h3 className="font-semibold text-white mb-4">My Applications</h3>
              {userAppsForThisBusiness.length === 0 ? (
                <p className="text-sm text-white/50 mb-4">No applications yet.</p>
              ) : (
                <div className="space-y-3 mb-4">
                  {userAppsForThisBusiness.map((app) => {
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
                  </div>

                  <div className="space-y-3">
                    <div>
                      <p className="text-xs font-medium text-white/40 uppercase tracking-wide">Description</p>
                      <p className="text-sm text-white/80 mt-1">{service.description}</p>
                    </div>

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
                <p className="text-white/60 text-center py-8">Sign in to manage checklists</p>
              ) : !currentAppId ? (
                <p className="text-white/60 text-center py-8">Select an application to view its checklist</p>
              ) : (
                <div className="space-y-4">
                  <div className="space-y-3">
                    {checklistItems.map((item) => (
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
                    ))}
                  </div>
                  <button
                    onClick={handleSaveChecklist}
                    disabled={trackerLoading}
                    className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors disabled:bg-blue-600/50"
                  >
                    {trackerLoading ? 'Saving...' : 'Save Checklist'}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* ─ FAQs Tab ─ */}
          {activeTab === 'faqs' && (
            <div className="space-y-4">
              {guidance.faqs.map((faq, idx) => (
                <div
                  key={idx}
                  className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6"
                >
                  <h3 className="text-lg font-semibold text-white mb-3">{faq.q}</h3>
                  <p className="text-white/80 text-sm">{faq.a}</p>
                </div>
              ))}
            </div>
          )}

          {/* ─ Legal Protections Tab ─ */}
          {activeTab === 'rights' && (
            <div className="space-y-4">
              <div className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Legal Protections</h3>
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
                  <h3 className="text-lg font-semibold text-white mb-4">Common Issues & Solutions</h3>
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
                <h3 className="text-sm font-semibold text-red-400 mb-2">Disclaimer</h3>
                <p className="text-xs text-red-400/80">{guidance.disclaimer}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ─ Create Application Modal ─ */}
      {showTrackerModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-white/10 rounded-lg max-w-md w-full p-6 space-y-4">
            <h2 className="text-xl font-bold text-white">Track New Application</h2>

            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">
                Service Type
              </label>
              <select
                value={selectedService}
                onChange={(e) => setSelectedService(e.target.value)}
                className="w-full rounded-lg border border-white/10 bg-white/[0.02] text-white p-2 text-sm"
              >
                <option value="">Select a service...</option>
                {guidance.services.map((service) => (
                  <option key={service.service} value={service.service}>
                    {service.service}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-white/80 mb-2">
                Notes (Optional)
              </label>
              <textarea
                value={trackerNotes}
                onChange={(e) => setTrackerNotes(e.target.value)}
                placeholder="Any additional notes..."
                className="w-full rounded-lg border border-white/10 bg-white/[0.02] text-white p-2 text-sm resize-none h-20"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowTrackerModal(false)}
                className="flex-1 rounded-lg border border-white/10 text-white px-4 py-2 text-sm font-medium hover:bg-white/[0.02] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateApplication}
                disabled={!selectedService || trackerLoading}
                className="flex-1 rounded-lg bg-blue-600 text-white px-4 py-2 text-sm font-medium hover:bg-blue-700 transition-colors disabled:bg-blue-600/50"
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
