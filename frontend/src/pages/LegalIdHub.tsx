import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { fetchIdTypes, fetchApplications } from '../store/legalIdSlice'
import type { LegalIdType } from '../types'

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
  <div className="content-wrap py-8 sm:py-10">
      <div className="section-card mx-auto max-w-7xl rounded-[32px] p-6 sm:p-8">
      {/* ─ Hero Section ─ */}
      <div className="">
        <div>
          <p className="section-eyebrow">Government Services</p>
          <h1 className="text-4xl font-bold text-white mt-4">
            Legal ID Hub
          </h1>
          <p className="text-sm mt-3 text-white/60">
            Guidance for 6 Indian government ID types — Aadhaar, PAN, Driving Licence, Passport, Voter ID, and Certificates
          </p>
        </div>
      </div>

      {/* ─ ID Type Cards Grid ─ */}
      <div className="content-wrap py-16">
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
              <div
                key={idType.key}
                onClick={() => handleCardClick(idType)}
                className="group rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-8 hover:bg-white/[0.05] hover:border-white/20 transition-all cursor-pointer"
              >
                <div className="text-4xl mb-4">{idType.icon}</div>
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
            ))}
          </div>
        )}
      </div>

      {/* ─ My Applications Panel ─ */}
      {token && (
        <div className="">
          <div className="content-wrap py-12">
            <h2 className="text-2xl font-bold text-white mb-8">My Applications</h2>

            {error && (
              <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 mb-8">
                <p className="text-red-400">{error}</p>
              </div>
            )}

            {applications.length === 0 && !error ? (
              <div className="rounded-lg border border-white/10 bg-white/[0.02] p-12 text-center">
                <p className="text-white/60 mb-6">You haven't tracked any applications yet.</p>
                <button
                  onClick={() => navigate('/legal-id/aadhaar')}
                  className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 font-medium text-white hover:bg-blue-700 transition-colors"
                >
                  Start an Application
                </button>
              </div>
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
                    <div
                      key={app.id}
                      onClick={() => navigate(`/legal-id/${app.id_type}`)}
                      className="rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-6 hover:bg-white/[0.05] hover:border-white/20 transition-all cursor-pointer"
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
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─ Call to Action for Non-Logged-In Users ─ */}
      {!token && (
        <div className="border-t border-white/10 bg-white/[0.02] backdrop-blur-sm">
          <div className="content-wrap py-12 text-center">
            <h2 className="text-2xl font-bold text-white mb-4">Track Your Application</h2>
            <p className="text-white/60 mb-8 max-w-lg mx-auto">
              Sign in to save your application progress, create checklists, and track your documents.
            </p>
            <button
              onClick={() => navigate('/login')}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-8 py-3 font-medium text-white hover:bg-blue-700 transition-colors"
            >
              Sign In to Track Applications
            </button>
          </div>
        </div>
      )}
    </div>
    </div>
    
  )
}
