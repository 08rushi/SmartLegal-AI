import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { HUB_ADAPTERS, HUB_BASE_PATH, type HubId } from './hubs/hubAdapters'
import { ServiceHub, type ServiceTypeItem, type ServiceApplicationItem } from './ServiceHub'

/**
 * Hub grid of service types for Legal ID, Property and Business (the pages are thin wrappers).
 * Layout is the original ServiceHub; strings come from the hub's own namespace.
 */
export default function HubPage({ hub }: { hub: HubId }) {
  const adapter = HUB_ADAPTERS[hub]
  const { i18n } = useTranslation()
  const { t: th } = useTranslation(adapter.ns)
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const snap = useAppSelector(adapter.select)
  const { isAuthenticated } = useAppSelector((state) => state.auth)
  const base = HUB_BASE_PATH[hub]

  // Refetch on language change: the server returns language-specific names and error text.
  useEffect(() => {
    adapter.fetchTypes(dispatch)
    if (isAuthenticated) adapter.fetchApps(dispatch)
  }, [adapter, dispatch, isAuthenticated, i18n.language])

  const typeName = (key: string, fallback: string) => th(`types.${key}`, { defaultValue: fallback })

  const serviceItems: ServiceTypeItem[] = snap.types.map((it) => ({
    key: it.key,
    name: typeName(it.key, it.display_name),
    description: th('itemDescription', { authority: it.authority, name: typeName(it.key, it.display_name) }),
    icon_slug: it.key,
  }))

  const mappedApps: ServiceApplicationItem[] = snap.apps.map((a) => ({
    id: a.id,
    service_name: a.service,
    type_label: typeName(a.type, a.type.replace(/_/g, ' ')),
    status: a.status,
    updated_at: a.updated_at,
    notes: a.notes,
  }))

  return (
    <ServiceHub
      title={th('title')}
      hubName={hub}
      eyebrow={th('eyebrow')}
      subtitle={th('subtitle')}
      items={serviceItems}
      applications={mappedApps}
      isLoading={snap.isLoading}
      error={snap.error}
      onSelectService={(item) => navigate(`${base}/${encodeURIComponent(item.key)}`)}
      onViewApplication={(appId) => {
        const app = snap.apps.find((a) => a.id === appId)
        if (app) navigate(`${base}/${encodeURIComponent(app.type)}`)
        else navigate('/tracker')
      }}
      onRetry={() => adapter.fetchTypes(dispatch)}
    />
  )
}
