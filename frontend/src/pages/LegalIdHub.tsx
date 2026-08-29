import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { fetchIdTypes, fetchApplications } from '../store/legalIdSlice'
import { ServiceHub, ServiceTypeItem, ServiceApplicationItem } from '../components/ServiceHub'

export default function LegalIdHub() {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { idTypes, applications, isLoading, error } = useAppSelector((state) => state.legalId)
  const { token } = useAppSelector((state) => state.auth)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return
    dispatch(fetchIdTypes())
    if (token) {
      dispatch(fetchApplications())
    }
  }, [mounted, dispatch, token])

  const serviceItems: ServiceTypeItem[] = idTypes.map((t) => ({
    key: t.key,
    name: t.display_name,
    description: `Official ${t.authority} identity documentation, application guidance, and verification checklists.`,
    icon_slug: t.key,
  }))

  const mappedApps: ServiceApplicationItem[] = applications.map((a) => ({
    id: a.id,
    service_name: a.service,
    type_label: a.id_type.replace(/_/g, ' '),
    status: a.status,
    updated_at: a.updated_at,
    notes: a.notes,
  }))

  return (
    <ServiceHub
      title="Legal ID Hub"
      hubName="legal-id"
      eyebrow="Indian Identity Services"
      subtitle="Comprehensive guidance for 6 Indian government ID types — Aadhaar, PAN, Driving Licence, Passport, Voter ID, and Official Certificates."

      items={serviceItems}
      applications={mappedApps}
      isLoading={isLoading}
      error={error}
      onSelectService={(item) => navigate(`/legal-id/${item.key}`)}
      onViewApplication={(appId) => {
        const app = applications.find((a) => a.id === appId)
        if (app) navigate(`/legal-id/${app.id_type}`)
        else navigate('/service-tracker')
      }}
      onRetry={() => dispatch(fetchIdTypes())}
    />
  )
}

