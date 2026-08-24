import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { fetchIdTypes, fetchApplications } from '../store/legalIdSlice'
import type { LegalIdType } from '../types'
import ServiceArt from '../components/ServiceArt'
import { Card } from '../components/Card'

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

  const handleCardClick = (idType: LegalIdType) => {
    navigate(`/legal-id/${idType.key}`)
  }

  return (
    <div className="content-wrap py-5 sm:py-6">
      <Card variant="section" className="mx-auto max-w-7xl rounded-[32px] p-6 sm:p-8">
        {/* ─ Hero Section ─ */}
        <div>
          <p className="section-eyebrow">Government Services</p>
          <h1 className="text-4xl font-bold text-white mt-4">
            Legal ID Hub
          </h1>
          <p className="text-sm mt-3 text-white/60">
            Guidance for 6 Indian government ID types — Aadhaar, PAN, Driving Licence, Passport, Voter ID, and Certificates
          </p>
        </div>

        {/* ─ ID Type Cards Grid ─ */}
        <div className="py-8">
          {isLoading ? (
            <div className="text-center py-12">
              <div className="inline-block">
                <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              </div>
              <p className="mt-4 text-white/40">Loading ID types...</p>
            </div>
          ) : error ? (
            <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6">
              <p className="text-red-400">{error}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {idTypes.map((idType) => (
                <Card
                  key={idType.key}
                  variant="section"
                  hoverLift
                  onClick={() => handleCardClick(idType)}
                  className="group hub-service-card relative overflow-hidden rounded-xl p-8 cursor-pointer"
                >
                  <div className="hub-service-card__art" aria-hidden="true">
                    <ServiceArt hub="legal-id" serviceKey={idType.key} />
                  </div>
                  <div className="relative z-10">
                    <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors">
                      {idType.display_name}
                    </h3>
                    <p className="text-sm text-white/60 mt-2">
                      {idType.authority}
                    </p>
                    <a
                      href={idType.official_portal}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="inline-block text-xs text-blue-400 hover:text-blue-300 mt-4 underline"
                    >
                      Official Portal →
                    </a>
                    <div className="mt-6 flex items-center text-sm text-blue-400 font-medium group-hover:translate-x-1 transition-transform">
                      View Guide
                      <span className="ml-2">→</span>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* ─ My Applications Panel ─ */}
        {token && (
          <div className="border-t border-white/10 pt-8">
            <h2 className="text-2xl font-bold text-white mb-8">My Applications</h2>

            {applications.length === 0 && !error ? (
              <Card variant="outline" className="p-12 text-center">
                <p className="text-white/60 mb-6">You haven't tracked any applications yet.</p>
                <button
                  onClick={() => navigate('/legal-id/aadhaar')}
                  className="btn-primary inline-flex items-center gap-2 px-6 py-3"
                >
                  Start an Application
                </button>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {applications.map((app) => {
                  const statusColors: Record<string, string> = {
                    in_progress: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400',
                    submitted: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
                    received: 'bg-green-500/10 border-green-500/20 text-green-400',
                    completed: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
                  }
                  const statusBgColor = statusColors[app.status] || 'bg-gray-500/10 border-gray-500/20 text-gray-400'

                  return (
                    <Card
                      key={app.id}
                      variant="outline"
                      hoverLift
                      onClick={() => navigate(`/legal-id/${app.id_type}`)}
                      className="p-6 cursor-pointer"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h4 className="font-semibold text-white">
                            {app.id_type
                              .replace(/_/g, ' ')
                              .split(' ')
                              .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                              .join(' ')}
                          </h4>
                          <p className="text-sm text-white/60">{app.service}</p>
                        </div>
                      </div>

                      <div className={`inline-block rounded px-3 py-1 text-xs font-medium border ${statusBgColor}`}>
                        {app.status.replace('_', ' ').charAt(0).toUpperCase() +
                          app.status.replace('_', ' ').slice(1)}
                      </div>

                      {app.notes && (
                        <p className="text-sm text-white/50 mt-4 line-clamp-2">
                          {app.notes}
                        </p>
                      )}

                      <p className="text-xs text-white/40 mt-4">
                        Updated {new Date(app.updated_at).toLocaleDateString()}
                      </p>
                    </Card>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* ─ Call to Action for Non-Logged-In Users ─ */}
        {!token && (
          <Card variant="outline" className="mt-8 p-8 text-center">
            <h2 className="text-2xl font-bold text-white mb-4">Track Your Application</h2>
            <p className="text-white/60 mb-8 max-w-lg mx-auto">
              Sign in to save your application progress, create checklists, and track your documents.
            </p>
            <button
              onClick={() => navigate('/login')}
              className="btn-primary inline-flex items-center gap-2 px-8 py-3"
            >
              Sign In to Track Applications
            </button>
          </Card>
        )}
      </Card>
    </div>
  )
}
