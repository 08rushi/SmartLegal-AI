import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { fetchPropertyTypes, fetchPropertyApplications } from '../store/propertySlice'
import type { PropertyType } from '../types'
import ServiceArt from '../components/ServiceArt'
import { Card } from '../components/Card'

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

  const handleCardClick = (propertyType: PropertyType) => {
    navigate(`/property-hub/${propertyType.key}`)
  }

  return (
    <div className="content-wrap py-5 sm:py-6">
      <Card variant="section" className="mx-auto max-w-7xl rounded-[32px] p-6 sm:p-8">
        {/* ─ Hero Section ─ */}
        <div>
          <p className="section-eyebrow">Government Services</p>
          <h1 className="text-4xl font-bold text-white mt-4">
            Property Hub
          </h1>
          <p className="text-sm mt-3 text-white/60">
            Guidance for 8 Indian property types — Sale, Rental, Mutation, Encumbrance, Registration, 7/12, Ferfar, Index II
          </p>
        </div>

        {/* ─ Property Type Cards Grid ─ */}
        <div className="py-8">
          {isLoading ? (
            <div className="text-center py-12">
              <div className="inline-block">
                <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              </div>
              <p className="mt-4 text-white/40">Loading property types...</p>
            </div>
          ) : error ? (
            <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6">
              <p className="text-red-400">{error}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {propertyTypes.map((propertyType) => (
                <Card
                  key={propertyType.key}
                  variant="section"
                  hoverLift
                  onClick={() => handleCardClick(propertyType)}
                  className="group hub-service-card relative overflow-hidden rounded-xl p-8 cursor-pointer"
                >
                  <div className="hub-service-card__art" aria-hidden="true">
                    <ServiceArt hub="property" serviceKey={propertyType.key} />
                  </div>
                  <div className="relative z-10">
                    <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors">
                      {propertyType.display_name}
                    </h3>
                    <p className="text-sm text-white/60 mt-2">
                      {propertyType.authority}
                    </p>
                    <a
                      href={propertyType.official_portal}
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

            {applications.length === 0 ? (
              <Card variant="outline" className="p-8 text-center">
                <p className="text-white/60">
                  No applications yet. Click on a property type to get started.
                </p>
              </Card>
            ) : (
              <div className="space-y-4">
                {applications.map((app) => (
                  <Card
                    key={app.id}
                    variant="outline"
                    hoverLift
                    className="p-6"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-white">
                          {app.property_type.charAt(0).toUpperCase() + app.property_type.slice(1)}
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
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ─ Login Prompt ─ */}
        {!token && (
          <Card variant="outline" className="mt-8 p-8 text-center">
            <p className="text-white/60 mb-4">
              Sign in to track your property applications
            </p>
            <button
              onClick={() => navigate('/login')}
              className="btn-primary inline-flex items-center gap-2 px-6 py-2"
            >
              Sign In
            </button>
          </Card>
        )}
      </Card>
    </div>
  )
}
