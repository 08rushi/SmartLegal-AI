import React from 'react'
import ServiceArt from './ServiceArt'
import { Card } from './Card'
import type { Hub } from '../lib/serviceColors'

export interface ServiceTypeItem {
  key: string
  name: string
  description: string
  steps_count?: number
  docs_count?: number
  icon_slug?: string
}

export interface ServiceApplicationItem {
  id: string
  service_name: string
  type_label: string
  status: string
  updated_at: string
  notes?: string
  checklist_done?: number
  checklist_total?: number
}

interface ServiceHubProps {
  title: string
  hubName?: Hub
  eyebrow?: string
  subtitle: string
  items: ServiceTypeItem[]
  applications?: ServiceApplicationItem[]
  isLoading?: boolean
  error?: string | null
  onSelectService: (item: ServiceTypeItem) => void
  onViewApplication?: (appId: string) => void
  onRetry?: () => void
}

export const ServiceHub: React.FC<ServiceHubProps> = ({
  title,
  hubName = 'legal-id',
  eyebrow = 'Civic & Legal Services',
  subtitle,
  items,
  applications = [],
  isLoading = false,
  error = null,
  onSelectService,
  onViewApplication,
  onRetry,
}) => {
  return (
    <div className="content-wrap py-5 sm:py-6">
      <Card variant="section" className="mx-auto max-w-7xl rounded-[32px] p-6 sm:p-8 space-y-8">
        
        {/* ─ Hero Header ─ */}
        <div>
          <p className="section-eyebrow">{eyebrow}</p>
          <h1 className="text-3xl sm:text-4xl font-bold text-white mt-2">
            {title}
          </h1>
          <p className="text-sm mt-2 text-white/60 max-w-3xl leading-relaxed">
            {subtitle}
          </p>
        </div>

        {/* ─ Service Types Grid ─ */}
        <div className="py-2">
          {isLoading ? (
            <div className="text-center py-12">
              <div className="inline-block">
                <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
              </div>
              <p className="mt-4 text-xs text-slate-400">Loading service catalog...</p>
            </div>
          ) : error ? (
            <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-6 text-center">
              <p className="text-sm text-red-400 font-semibold">{error}</p>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="mt-4 px-4 py-2 text-xs font-semibold rounded-xl bg-white/10 text-white hover:bg-white/20 transition-all"
                >
                  Retry Loading
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {items.map((item) => (
                <div
                  key={item.key}
                  onClick={() => onSelectService(item)}
                  className="group bg-slate-900/80 border border-slate-800 hover:border-indigo-500/50 rounded-2xl p-6 transition-all duration-300 shadow-xl hover:shadow-indigo-500/10 cursor-pointer flex flex-col justify-between"
                >
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400 group-hover:scale-110 transition-transform">
                        <ServiceArt hub={hubName} serviceKey={item.icon_slug || item.key} className="w-6 h-6" />
                      </div>
                      {item.steps_count !== undefined && (
                        <span className="text-[11px] font-semibold text-slate-400 bg-slate-950 border border-slate-800 px-2.5 py-1 rounded-lg">
                          {item.steps_count} Steps
                        </span>
                      )}
                    </div>


                    <div>
                      <h3 className="text-base font-bold text-white group-hover:text-indigo-300 transition-colors">
                        {item.name}
                      </h3>
                      <p className="text-xs text-slate-400 mt-1.5 leading-relaxed line-clamp-3">
                        {item.description}
                      </p>
                    </div>
                  </div>

                  <div className="pt-4 mt-4 border-t border-slate-800/80 flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-indigo-400 group-hover:underline">
                      Explore Application Guide
                    </span>
                    <span className="text-xs text-indigo-400 group-hover:translate-x-1 transition-transform">
                      →
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ─ User Active Applications Tracker Section ─ */}
        {applications.length > 0 && (
          <div className="pt-6 border-t border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>📋</span> My Active Service Applications ({applications.length})
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {applications.map((app) => (
                <div
                  key={app.id}
                  onClick={() => onViewApplication && onViewApplication(app.id)}
                  className="bg-slate-900/60 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 transition-all cursor-pointer flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="px-2.5 py-0.5 text-[10px] font-bold uppercase rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                        {app.type_label}
                      </span>
                      <span className={`px-2.5 py-0.5 text-[10px] font-bold uppercase rounded-md border ${
                        app.status === 'completed'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                      }`}>
                        {app.status.replace('_', ' ')}
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-white">{app.service_name}</h4>
                    {app.notes && (
                      <p className="text-xs text-slate-400 line-clamp-1 italic bg-slate-950/60 p-2 rounded-lg border border-slate-800">
                        "{app.notes}"
                      </p>
                    )}
                  </div>

                  <div className="pt-3 mt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                    <span>Updated: {new Date(app.updated_at).toLocaleDateString()}</span>
                    <span className="font-semibold text-indigo-400 hover:underline">View Tracker →</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      </Card>
    </div>
  )
}

export default ServiceHub
