import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { fetchApplications as fetchLegalIdApplications } from '../store/legalIdSlice'
import { fetchPropertyApplications } from '../store/propertySlice'
import { fetchBusinessApplications } from '../store/businessSlice'
import { Card } from '../components/Card'

type TrackerKind = 'legal-id' | 'property' | 'business' | 'yojana'

interface TrackerApplication {
  id: string
  kind: TrackerKind
  label: string
  type: string
  service: string
  status: 'in_progress' | 'submitted' | 'received' | 'completed'
  notes: string
  updated_at: string
  detailPath: string
}

interface Reminder {
  appId: string
  remindAt: string
  note: string
  notifiedAt?: string
}

const STORAGE_KEY = 'sl_service_tracker_reminders'

const statusLabel: Record<TrackerApplication['status'], string> = {
  in_progress: 'In progress',
  submitted: 'Submitted',
  received: 'Received',
  completed: 'Completed',
}

const statusClass: Record<TrackerApplication['status'], string> = {
  in_progress: 'border-yellow-500/25 bg-yellow-500/10 text-yellow-200',
  submitted: 'border-blue-500/25 bg-blue-500/10 text-blue-200',
  received: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-200',
  completed: 'border-[#f5c26b]/25 bg-[#f5c26b]/10 text-[#f5c26b]',
}

const serviceLabel: Record<TrackerKind, string> = {
  'legal-id': 'Legal ID',
  property: 'Property',
  business: 'Business',
  yojana: 'Jan-Yojana',
}


function readReminders(): Reminder[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function writeReminders(reminders: Reminder[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(reminders))
}

function formatName(value: string) {
  return value
    .replace(/[-_]/g, ' ')
    .split(' ')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

function toDateTimeLocal(value?: string) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const offset = date.getTimezoneOffset()
  const local = new Date(date.getTime() - offset * 60 * 1000)
  return local.toISOString().slice(0, 16)
}

function fromDateTimeLocal(value: string) {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '' : date.toISOString()
}

export default function ServiceTracker() {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { token } = useAppSelector((state) => state.auth)
  const legalId = useAppSelector((state) => state.legalId)
  const property = useAppSelector((state) => state.property)
  const business = useAppSelector((state) => state.business)
  const [reminders, setReminders] = useState<Reminder[]>(() => readReminders())
  const [notificationStatus, setNotificationStatus] = useState<NotificationPermission | 'unsupported'>(
    typeof Notification === 'undefined' ? 'unsupported' : Notification.permission
  )

  useEffect(() => {
    if (!token) return
    dispatch(fetchLegalIdApplications())
    dispatch(fetchPropertyApplications())
    dispatch(fetchBusinessApplications())
  }, [dispatch, token])

  useEffect(() => {
    writeReminders(reminders)
  }, [reminders])

  const applications = useMemo<TrackerApplication[]>(() => {
    const legalIdApps = legalId.applications.map((app) => ({
      id: app.id,
      kind: 'legal-id' as const,
      label: serviceLabel['legal-id'],
      type: app.id_type,
      service: app.service,
      status: app.status,
      notes: app.notes,
      updated_at: app.updated_at,
      detailPath: `/legal-id/${app.id_type}`,
    }))

    const propertyApps = property.applications.map((app) => ({
      id: app.id,
      kind: 'property' as const,
      label: serviceLabel.property,
      type: app.property_type,
      service: app.service,
      status: app.status,
      notes: app.notes,
      updated_at: app.updated_at,
      detailPath: `/property-hub/${app.property_type}`,
    }))

    const businessApps = business.applications.map((app) => ({
      id: app.id,
      kind: 'business' as const,
      label: serviceLabel.business,
      type: app.business_type,
      service: app.service,
      status: app.status,
      notes: app.notes,
      updated_at: app.updated_at,
      detailPath: `/business-hub/${app.business_type}`,
    }))

    return [...legalIdApps, ...propertyApps, ...businessApps].sort(
      (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    )
  }, [business.applications, legalId.applications, property.applications])

  useEffect(() => {
    if (notificationStatus !== 'granted') return

    const notifyDueReminders = () => {
      const now = Date.now()
      const due = reminders.filter((reminder) => {
        if (!reminder.remindAt || reminder.notifiedAt) return false
        return new Date(reminder.remindAt).getTime() <= now
      })

      if (due.length === 0) return

      const nextReminders = reminders.map((reminder) => {
        const matchingApp = applications.find((app) => app.id === reminder.appId)
        const isDue = due.some((item) => item.appId === reminder.appId)
        if (!isDue || !matchingApp) return reminder

        new Notification('SmartLegal AI reminder', {
          body: `${matchingApp.service}: ${reminder.note || 'Follow up on this application.'}`,
        })

        return { ...reminder, notifiedAt: new Date().toISOString() }
      })

      setReminders(nextReminders)
    }

    notifyDueReminders()
    const interval = window.setInterval(notifyDueReminders, 60 * 1000)
    return () => window.clearInterval(interval)
  }, [applications, notificationStatus, reminders])

  const isLoading = legalId.isLoading || property.isLoading || business.isLoading
  const activeCount = applications.filter((app) => app.status !== 'completed').length
  const completedCount = applications.filter((app) => app.status === 'completed').length
  const upcomingReminders = reminders.filter((reminder) => reminder.remindAt && !reminder.notifiedAt).length

  const setReminder = (appId: string, field: 'remindAt' | 'note', value: string) => {
    setReminders((current) => {
      const existing = current.find((reminder) => reminder.appId === appId)
      const nextValue = field === 'remindAt' ? fromDateTimeLocal(value) : value
      if (!existing) {
        return [...current, { appId, remindAt: field === 'remindAt' ? nextValue : '', note: field === 'note' ? value : '' }]
      }
      return current.map((reminder) =>
        reminder.appId === appId ? { ...reminder, [field]: nextValue, notifiedAt: undefined } : reminder
      )
    })
  }

  const clearReminder = (appId: string) => {
    setReminders((current) => current.filter((reminder) => reminder.appId !== appId))
  }

  const requestNotifications = async () => {
    if (typeof Notification === 'undefined') {
      setNotificationStatus('unsupported')
      return
    }
    const result = await Notification.requestPermission()
    setNotificationStatus(result)
  }

  if (!token) {
    return (
      <div className="content-wrap py-8">
        <Card variant="glass" className="mx-auto max-w-2xl rounded-[28px] p-8 text-center">
          <p className="section-eyebrow">Service Tracker</p>
          <h1 className="mt-4 text-3xl font-bold text-white">Sign in to track applications</h1>
          <p className="mt-3 text-slate-400">
            Track Legal ID, Property, and Business License applications with saved checklists and reminders.
          </p>
          <div className="mt-8 flex justify-center gap-3">
            <Link to="/login" className="btn-primary">Login</Link>
            <Link to="/services" className="btn-secondary">View Services</Link>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="content-wrap py-7">
      <div className="mb-8 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="section-eyebrow">4D Tracker</p>
          <h1 className="mt-4 text-4xl font-bold text-white">Service Tracker</h1>
          <p className="mt-3 max-w-2xl text-slate-400">
            One place for your service applications, checklist follow-ups, and reminder notifications.
          </p>
        </div>
        <button
          type="button"
          onClick={requestNotifications}
          disabled={notificationStatus === 'granted' || notificationStatus === 'unsupported'}
          className="btn-secondary"
        >
          {notificationStatus === 'granted'
            ? 'Notifications On'
            : notificationStatus === 'unsupported'
              ? 'Notifications Unavailable'
              : 'Enable Notifications'}
        </button>
      </div>

      <div className="mb-8 grid gap-4 md:grid-cols-3">
        <Card variant="metric" className="rounded-[22px] p-5">
          <p className="text-sm text-slate-500">Active</p>
          <p className="mt-2 text-3xl font-semibold text-white">{activeCount}</p>
        </Card>
        <Card variant="metric" className="rounded-[22px] p-5">
          <p className="text-sm text-slate-500">Completed</p>
          <p className="mt-2 text-3xl font-semibold text-white">{completedCount}</p>
        </Card>
        <Card variant="metric" className="rounded-[22px] p-5">
          <p className="text-sm text-slate-500">Reminders</p>
          <p className="mt-2 text-3xl font-semibold text-white">{upcomingReminders}</p>
        </Card>
      </div>

      {isLoading && applications.length === 0 ? (
        <Card variant="glass" className="rounded-[28px] p-10 text-center text-slate-400">Loading tracker...</Card>
      ) : applications.length === 0 ? (
        <Card variant="glass" className="rounded-[28px] p-10 text-center">
          <h2 className="text-2xl font-semibold text-white">No tracked applications yet</h2>
          <p className="mt-3 text-slate-400">Start from a service hub, create an application tracker, then it will appear here.</p>
          <button type="button" onClick={() => navigate('/services')} className="btn-primary mt-6">
            Browse Services
          </button>
        </Card>
      ) : (
        <div className="grid gap-5">
          {applications.map((app) => {
            const reminder = reminders.find((item) => item.appId === app.id)
            return (
              <Card
                key={`${app.kind}-${app.id}`}
                as="article"
                variant="glass"
                className={`hub-service-card hub-service-card--${app.kind} rounded-[24px] p-5`}
              >
                <div className="hub-service-card__art" aria-hidden="true">
                  <span />
                  <span />
                  <span />
                </div>
                <div className="relative z-10 grid gap-5 lg:grid-cols-[1fr_360px] lg:items-start">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs font-medium text-slate-300">
                        {app.label}
                      </span>
                      <span className={`rounded-full border px-3 py-1 text-xs font-medium ${statusClass[app.status]}`}>
                        {statusLabel[app.status]}
                      </span>
                    </div>
                    <h2 className="mt-4 text-xl font-semibold text-white">{formatName(app.type)}</h2>
                    <p className="mt-1 text-sm text-slate-300">{app.service}</p>
                    {app.notes && <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-500">{app.notes}</p>}
                    <div className="mt-5 flex flex-wrap items-center gap-3">
                      <Link to={app.detailPath} className="btn-secondary px-4 py-2">
                        Open Checklist
                      </Link>
                      <span className="text-xs text-slate-500">
                        Updated {new Date(app.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  <div className="rounded-[18px] border border-white/10 bg-white/[0.03] p-4">
                    <label className="block text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                      Reminder
                    </label>
                    <input
                      type="datetime-local"
                      value={toDateTimeLocal(reminder?.remindAt)}
                      onChange={(event) => setReminder(app.id, 'remindAt', event.target.value)}
                      className="input-field mt-3"
                    />
                    <textarea
                      value={reminder?.note || ''}
                      onChange={(event) => setReminder(app.id, 'note', event.target.value)}
                      placeholder="Follow-up note"
                      className="input-field mt-3 min-h-20 resize-none"
                    />
                    <div className="mt-3 flex items-center justify-between gap-3">
                      <p className="text-xs text-slate-500">
                        {reminder?.notifiedAt ? 'Notification sent' : reminder?.remindAt ? 'Reminder saved' : 'No reminder set'}
                      </p>
                      {reminder && (
                        <button
                          type="button"
                          onClick={() => clearReminder(app.id)}
                          className="text-xs font-medium text-[#fb7185] hover:text-[#fda4af]"
                        >
                          Clear
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
