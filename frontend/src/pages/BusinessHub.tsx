import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { fetchBusinessTypes, fetchBusinessApplications } from '../store/businessSlice'
import type { BusinessType } from '../types'

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

  const handleCardClick = (businessType: BusinessType) => {
    navigate(`/business-hub/${businessType.key}`)
  }

  return (
    // <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800">
    //   {/* ─ Hero Section ─ */}
    //   <div className="border-b border-white/10 bg-white/[0.02] backdrop-blur-sm">
    //     <div className="content-wrap space-y-2 py-12">
    //       <p className="section-eyebrow">Government Services</p>
    //       <h1 className="text-4xl font-bold text-white">
    //         Business License Hub
    //       </h1>
    //       <p className="text-lg text-white/60">
    //         Guidance for 9 Indian business registrations — GST, FSSAI, MSME, Shop Act, IEC, Trade License, Professional Tax, PAN/TAN, Startup India
    //       </p>
    //     </div>
    //   </div>


      <div className="content-wrap py-8 sm:py-10">
      <div className="section-card mx-auto max-w-7xl rounded-[32px] p-6 sm:p-8">
      {/* ─ Hero Section ─ */}
      <div className="">
        <div>
          <p className="section-eyebrow">Government Services</p>
          <h1 className="text-4xl font-bold text-white mt-4">
            Business License Hub
          </h1>
          <p className="text-sm mt-3 text-white/60">
           Guidance for 9 Indian business registrations — GST, FSSAI, MSME, Shop Act, IEC, Trade License, Professional Tax, PAN/TAN, Startup India
          </p>
        </div>
      </div>

      {/* ─ Business Type Cards Grid ─ */}
      <div className="content-wrap py-16">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block">
              <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            </div>
            <p className="mt-4 text-white/40">Loading business types...</p>
          </div>
        ) : error ? (
          <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6">
            <p className="text-red-400">{error}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {businessTypes.map((businessType) => (
              <div
                key={businessType.key}
                onClick={() => handleCardClick(businessType)}
                className="group rounded-lg border border-white/10 bg-white/[0.02] backdrop-blur-sm p-8 hover:bg-white/[0.05] hover:border-white/20 transition-all cursor-pointer"
              >
                <div className="text-4xl mb-4">{businessType.icon}</div>
                <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors">
                  {businessType.display_name}
                </h3>
                <p className="text-sm text-white/60 mt-2">
                  {businessType.authority}
                </p>
                <a
                  href={businessType.official_portal}
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
        <div className="border-t border-white/10 bg-white/[0.02] backdrop-blur-sm">
          <div className="content-wrap py-12">
            <h2 className="text-2xl font-bold text-white mb-8">My Applications</h2>

            {error && (
              <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 mb-8">
                <p className="text-red-400">{error}</p>
              </div>
            )}

            {applications.length === 0 ? (
              <div className="rounded-lg border border-white/10 bg-white/[0.02] p-8 text-center">
                <p className="text-white/60">
                  No applications yet. Click on a business registration type to get started.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {applications.map((app) => (
                  <div
                    key={app.id}
                    className="rounded-lg border border-white/10 bg-white/[0.02] p-6 hover:bg-white/[0.05] transition-all"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-white">
                          {app.business_type.charAt(0).toUpperCase() + app.business_type.slice(1)}
                        </h3>
                        <p className="text-sm text-white/60 mt-1">
                          {app.service}
                        </p>
                        {app.notes && (
                          <p className="text-sm text-white/50 mt-2">
                            {app.notes}
                          </p>
                        )}
                      </div>
                      <div className="text-right">
                        <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                          app.status === 'completed'
                            ? 'bg-green-500/20 text-green-400'
                            : app.status === 'submitted'
                            ? 'bg-blue-500/20 text-blue-400'
                            : 'bg-yellow-500/20 text-yellow-400'
                        }`}>
                          {app.status}
                        </span>
                        <p className="text-xs text-white/40 mt-2">
                          {new Date(app.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─ Login Prompt ─ */}
      {!token && (
        <div className="border-t border-white/10 bg-white/[0.02] backdrop-blur-sm">
          <div className="content-wrap py-12 text-center">
            <p className="text-white/60 mb-4">
              Sign in to track your business registrations
            </p>
            <button
              onClick={() => navigate('/login')}
              className="inline-block px-6 py-2 rounded-lg bg-blue-500 hover:bg-blue-600 text-white font-medium transition-colors"
            >
              Sign In
            </button>
          </div>
        </div>
      )}
    </div>
    </div>
  )
}
