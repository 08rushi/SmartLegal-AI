import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { fetchBusinessTypes, fetchBusinessApplications } from '../store/businessSlice'
import { ServiceHub, ServiceTypeItem, ServiceApplicationItem } from '../components/ServiceHub'

export default function BusinessHub() {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { businessTypes, applications, isLoading, error } = useAppSelector((state) => state.business)
  const { token } = useAppSelector((state) => state.auth)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return
    dispatch(fetchBusinessTypes())
    if (token) {
      dispatch(fetchBusinessApplications())
    }
  }, [mounted, dispatch, token])

  const serviceItems: ServiceTypeItem[] = businessTypes.map((t) => ({
    key: t.key,
    name: t.display_name,
    description: `Official business license registration, compliance guidance, and checklist for ${t.display_name}.`,
    icon_slug: t.key,
  }))

  const mappedApps: ServiceApplicationItem[] = applications.map((a) => ({
    id: a.id,
    service_name: a.service,
    type_label: a.business_type.replace(/_/g, ' '),
    status: a.status,
    updated_at: a.updated_at || a.created_at,
    notes: a.notes,
  }))

  return (
    <ServiceHub
      title="Business License Hub"
      hubName="business"
      eyebrow="Commercial & Business Licensing Services"
      subtitle="Guidance for 9 Indian business registrations — GST, FSSAI Food License, MSME Udyam, Shop Act, Import Export Code (IEC), Trade License, Professional Tax, PAN/TAN, and Startup India."

      items={serviceItems}
      applications={mappedApps}
      isLoading={isLoading}
      error={error}
      onSelectService={(item) => navigate(`/business-hub/${item.key}`)}
      onViewApplication={(appId) => {
        const app = applications.find((a) => a.id === appId)
        if (app) navigate(`/business-hub/${app.business_type}`)
        else navigate('/service-tracker')
      }}
      onRetry={() => dispatch(fetchBusinessTypes())}
    />
  )
}

