import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { fetchApplications as fetchLegalIdApplications } from '../store/legalIdSlice'
import { fetchPropertyApplications } from '../store/propertySlice'
import { fetchBusinessApplications } from '../store/businessSlice'
import { Card } from '../components/Card'
import { formatLocalDate } from '../utils/i18nHelpers'

type TrackerKind = 'legal-id' | 'property' | 'business' | 'yojana'

interface TrackerApplication {
  id: string
  kind: TrackerKind
  type: string
  service: string
  status: string
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

const statusClass: Record<string, string> = {
  in_progress: 'border-yellow-500/25 bg-yellow-500/10 text-yellow-200',
  submitted: 'border-blue-500/25 bg-blue-500/10 text-blue-200',
  received: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-200',
  completed: 'border-[#f5c26b]/25 bg-[#f5c26b]/10 text-[#f5c26b]',
}

// i18n keys: tracker:kinds.<key> (label) and <ns>:types.<type> (service type name).
const kindKey: Record<TrackerKind, string> = {
  'legal-id': 'legalId',
  property: 'property',
  business: 'business',
  yojana: 'yojana',
}

const kindNamespace: Record<TrackerKind, string> = {
  'legal-id': 'legalid',
  property: 'property',
  business: 'business',
  yojana: 'tracker',
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
  const { t } = useTranslation('tracker')
  const { t: th } = useTranslation('hubs')
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { isAuthenticated } = useAppSelector((state) => state.auth)
  const legalId = useAppSelector((state) => state.legalId)
  const property = useAppSelector((state) => state.property)
  const business = useAppSelector((state) => state.business)
  const [reminders, setReminders] = useState<Reminder[]>(() => readReminders())
  const [notificationStatus, setNotificationStatus] = useState<NotificationPermission | 'unsupported'>(
    typeof Notification === 'undefined' ? 'unsupported' : Notification.permission
  )

  useEffect(() => {
    if (!isAuthenticated) return
    dispatch(fetchLegalIdApplications())
    dispatch(fetchPropertyApplications())
    dispatch(fetchBusinessApplications())
  }, [dispatch, isAuthenticated])

  useEffect(() => {
    writeReminders(reminders)
  }, [reminders])

  const applications = useMemo<TrackerApplication[]>(() => {
    const legalIdApps = legalId.applications.map((app) => ({
      id: app.id,
      kind: 'legal-id' as const,
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

        new Notification(t('notifications.title'), {
          body: t('notifications.body', {
            service: matchingApp.service,
            note: reminder.note || t('notifications.defaultNote'),
          }),
        })

        return { ...reminder, notifiedAt: new Date().toISOString() }
      })

      setReminders(nextReminders)
    }

    notifyDueReminders()
    const interval = window.setInterval(notifyDueReminders, 60 * 1000)
    return () => window.clearInterval(interval)
  }, [applications, notificationStatus, reminders, t])

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

  if (!isAuthenticated) {
    return (
      <div className="content-wrap py-8">
        <Card variant="glass" className="mx-auto max-w-2xl rounded-[28px] p-8 text-center">
          <p className="section-eyebrow">{t('eyebrow')}</p>
          <h1 className="mt-4 text-3xl font-bold text-white">{t('signIn.title')}</h1>
          <p className="mt-3 text-slate-400">
            {t('signIn.body')}
          </p>
          <div className="mt-8 flex justify-center gap-3">
            <Link to="/login" className="btn-primary">{t('signIn.login')}</Link>
            <Link to="/services" className="btn-secondary">{t('signIn.viewServices')}</Link>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="content-wrap py-7">
      <div className="mb-8 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="section-eyebrow">{t('eyebrowMain')}</p>
          <h1 className="mt-4 text-4xl font-bold text-white">{t('title')}</h1>
          <p className="mt-3 max-w-2xl text-slate-400">
            {t('subtitle')}
          </p>
        </div>
        <button
          type="button"
          onClick={requestNotifications}
          disabled={notificationStatus === 'granted' || notificationStatus === 'unsupported'}
          className="btn-secondary"
        >
          {notificationStatus === 'granted'
            ? t('notifications.on')
            : notificationStatus === 'unsupported'
              ? t('notifications.unavailable')
              : t('notifications.enable')}
        </button>
      </div>

      <div className="mb-8 grid gap-4 md:grid-cols-3">
        <Card variant="metric" className="rounded-[22px] p-5">
          <p className="text-sm text-slate-500">{t('stats.active')}</p>
          <p className="mt-2 text-3xl font-semibold text-white">{activeCount}</p>
        </Card>
        <Card variant="metric" className="rounded-[22px] p-5">
          <p className="text-sm text-slate-500">{t('stats.completed')}</p>
          <p className="mt-2 text-3xl font-semibold text-white">{completedCount}</p>
        </Card>
        <Card variant="metric" className="rounded-[22px] p-5">
          <p className="text-sm text-slate-500">{t('stats.reminders')}</p>
          <p className="mt-2 text-3xl font-semibold text-white">{upcomingReminders}</p>
        </Card>
      </div>

      {isLoading && applications.length === 0 ? (
        <Card variant="glass" className="rounded-[28px] p-10 text-center text-slate-400">{t('loading')}</Card>
      ) : applications.length === 0 ? (
        <Card variant="glass" className="rounded-[28px] p-10 text-center">
          <h2 className="text-2xl font-semibold text-white">{t('empty.title')}</h2>
          <p className="mt-3 text-slate-400">{t('empty.body')}</p>
          <button type="button" onClick={() => navigate('/services')} className="btn-primary mt-6">
            {t('empty.cta')}
          </button>
        </Card>
      ) : (
        <div className="grid gap-5">
          {applications.map((app) => {
            const reminder = reminders.find((item) => item.appId === app.id)
            const typeName = t(`${kindNamespace[app.kind]}:types.${app.type}`, { defaultValue: formatName(app.type) })
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
                        {t(`kinds.${kindKey[app.kind]}`)}
                      </span>
                      <span className={`rounded-full border px-3 py-1 text-xs font-medium ${statusClass[app.status] ?? statusClass.in_progress}`}>
                        {th(`status.${app.status}`, { defaultValue: app.status })}
                      </span>
                    </div>
                    <h2 className="mt-4 text-xl font-semibold text-white">{typeName}</h2>
                    <p className="mt-1 text-sm text-slate-300">{app.service}</p>
                    {app.notes && <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-500">{app.notes}</p>}
                    <div className="mt-5 flex flex-wrap items-center gap-3">
                      <Link to={app.detailPath} className="btn-secondary px-4 py-2">
                        {t('card.openChecklist')}
                      </Link>
                      <span className="text-xs text-slate-500">
                        {t('card.updated', { date: formatLocalDate(app.updated_at) })}
                      </span>
                    </div>
                  </div>

                  <div className="rounded-[18px] border border-white/10 bg-white/[0.03] p-4">
                    <label className="block text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                      {t('reminder.label')}
                    </label>
                    <input
                      type="datetime-local"
                      aria-label={t('reminder.dateLabel')}
                      value={toDateTimeLocal(reminder?.remindAt)}
                      onChange={(event) => setReminder(app.id, 'remindAt', event.target.value)}
                      className="input-field mt-3"
                    />
                    <textarea
                      value={reminder?.note || ''}
                      onChange={(event) => setReminder(app.id, 'note', event.target.value)}
                      placeholder={t('reminder.notePlaceholder')}
                      aria-label={t('reminder.notePlaceholder')}
                      className="input-field mt-3 min-h-20 resize-none"
                    />
                    <div className="mt-3 flex items-center justify-between gap-3">
                      <p className="text-xs text-slate-500">
                        {reminder?.notifiedAt ? t('reminder.sent') : reminder?.remindAt ? t('reminder.saved') : t('reminder.none')}
                      </p>
                      {reminder && (
                        <button
                          type="button"
                          onClick={() => clearReminder(app.id)}
                          className="text-xs font-medium text-[#fb7185] hover:text-[#fda4af]"
                        >
                          {t('reminder.clear')}
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
