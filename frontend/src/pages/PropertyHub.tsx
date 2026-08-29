import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { fetchPropertyTypes, fetchPropertyApplications } from '../store/propertySlice'
import { ServiceHub, ServiceTypeItem, ServiceApplicationItem } from '../components/ServiceHub'

export default function PropertyHub() {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { propertyTypes, applications, isLoading, error } = useAppSelector((state) => state.property)
  const { token } = useAppSelector((state) => state.auth)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return
    dispatch(fetchPropertyTypes())
    if (token) {
      dispatch(fetchPropertyApplications())
    }
  }, [mounted, dispatch, token])

  const serviceItems: ServiceTypeItem[] = propertyTypes.map((t) => ({
    key: t.key,
    name: t.display_name,
    description: `Official property legal guidance, application checklists, and document verification for ${t.display_name}.`,
    icon_slug: t.key,
  }))

  const mappedApps: ServiceApplicationItem[] = applications.map((a) => ({
    id: a.id,
    service_name: a.service,
    type_label: a.property_type.replace(/_/g, ' '),
    status: a.status,
    updated_at: a.updated_at,
    notes: a.notes,
  }))

  return (
    <ServiceHub
      title="Property Hub"
      hubName="property"
      eyebrow="Real Estate & Land Registry Services"
      subtitle="Guidance for 8 Indian property document types — Sale Deed, Rental Agreement, Land Mutation, Encumbrance Certificate, Property Registration, 7/12 Extract, Ferfar, and Index II."

      items={serviceItems}
      applications={mappedApps}
      isLoading={isLoading}
      error={error}
      onSelectService={(item) => navigate(`/property-hub/${item.key}`)}
      onViewApplication={(appId) => {
        const app = applications.find((a) => a.id === appId)
        if (app) navigate(`/property-hub/${app.property_type}`)
        else navigate('/service-tracker')
      }}
      onRetry={() => dispatch(fetchPropertyTypes())}
    />
  )
}
