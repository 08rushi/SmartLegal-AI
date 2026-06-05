import { useNavigate } from 'react-router-dom'
import { useAppSelector } from '../hooks/redux'

interface ServiceCard {
  key: string
  title: string
  description: string
  icon: string
  route: string
  badge?: string
  color: 'blue' | 'purple' | 'green' | 'orange' | 'pink'
}

const services: ServiceCard[] = [
  {
    key: 'legal-id',
    title: 'Legal ID Hub',
    description: 'Government ID guidance — Aadhaar, PAN, Passport, Driving License, Voter ID & Certificates',
    icon: '🆔',
    route: '/legal-id',
    color: 'blue',
    badge: 'Popular'
  },
  {
    key: 'property',
    title: 'Property Hub',
    description: 'Property transaction guidance — Sale, Rental, Mutation, Registration & Encumbrance Certificate',
    icon: '🏠',
    route: '/property-hub',
    color: 'green',
    badge: 'Popular'
  },
  {
    key: 'business',
    title: 'Business License Hub',
    description: 'Business registration guidance - GST, FSSAI, MSME, Shop Act, IEC, Trade License & Startup India',
    icon: 'BIZ',
    route: '/business-hub',
    color: 'orange',
    badge: 'New'
  },
  {
    key: 'tracker',
    title: 'Service Tracker',
    description: 'Track applications, save checklists, set reminders, and enable browser notifications',
    icon: '4D',
    route: '/tracker',
    color: 'pink',
    badge: '4D'
  },
  {
    key: 'documents',
    title: 'Document Analysis',
    description: 'Upload and analyze legal documents — Get risk assessments and plain-language explanations',
    icon: '📄',
    route: '/upload',
    color: 'purple'
  },
  {
    key: 'chat',
    title: 'AI Legal Assistant',
    description: 'Ask questions about your documents — Get instant answers and clause clarifications',
    icon: '💬',
    route: '/chat',
    color: 'orange'
  }
]

const colorMap = {
  blue: 'border-blue-500/20 bg-blue-500/5 hover:bg-blue-500/10 group-hover:text-blue-400',
  purple: 'border-purple-500/20 bg-purple-500/5 hover:bg-purple-500/10 group-hover:text-purple-400',
  green: 'border-green-500/20 bg-green-500/5 hover:bg-green-500/10 group-hover:text-green-400',
  orange: 'border-orange-500/20 bg-orange-500/5 hover:bg-orange-500/10 group-hover:text-orange-400',
  pink: 'border-pink-500/20 bg-pink-500/5 hover:bg-pink-500/10 group-hover:text-pink-400'
}

const badgeColorMap = {
  blue: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  purple: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  green: 'bg-green-500/20 text-green-400 border-green-500/30',
  orange: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  pink: 'bg-pink-500/20 text-pink-400 border-pink-500/30'
}

export default function ServicesHub() {
  const navigate = useNavigate()
  const { token } = useAppSelector((state) => state.auth)

  return (
    <div className="content-wrap py-8 sm:py-10">
      <div className="section-card mx-auto max-w-7xl rounded-[32px] p-6 sm:p-8">
      {/* ─ Hero Section ─ */}
      <div className="">
        <div>
          <h1 className="text-4xl font-bold text-white mt-4">
            Online Service Center
          </h1>
            <p className="text-sm mt-3 text-white/60">
              Complete legal guidance for Indians — from government IDs to property transactions to document analysis
            </p>
          </div>
          <div className="flex flex-wrap gap-3 text-sm mt-2">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-2 py-2">
              <span className="text-base">✓</span> Expert Guidance
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-2 py-2">
              <span className="text-base">✓</span> Hindi & English
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-2 py-2">
              <span className="text-base">✓</span> AI-Powered
            </span>
          </div>
        </div>
      </div>

      {/* Services Grid */}
      <div className="content-wrap py-20">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {services.map((service) => (
            <div
              key={service.key}
              onClick={() => navigate(service.route)}
              className={`group relative overflow-hidden rounded-2xl border border-white/10 p-8 transition-all duration-300 cursor-pointer hover:border-white/20 ${colorMap[service.color]}`}
            >
              {/* Background gradient accent */}
              <div className="absolute -right-16 -top-16 h-32 w-32 rounded-full bg-white/5 group-hover:bg-white/10 transition-all duration-300 hover-lift" />

              <div className="relative z-10 space-y-4">
                {/* Icon & Badge */}
                <div className="flex items-start justify-between">
                  <span className="text-5xl">{service.icon}</span>
                  {service.badge && (
                    <span className={`inline-block rounded-full px-3 py-1 text-xs font-semibold border ${badgeColorMap[service.color]}`}>
                      {service.badge}
                    </span>
                  )}
                </div>

                {/* Title & Description */}
                <div>
                  <h3 className="text-2xl font-bold text-white group-hover:text-white transition-colors">
                    {service.title}
                  </h3>
                  <p className="mt-3 text-sm text-white/60 leading-relaxed">
                    {service.description}
                  </p>
                </div>

                {/* CTA */}
                <div className="flex items-center gap-2 text-sm font-medium text-white/70 group-hover:text-white transition-colors pt-4">
                  <span>Explore</span>
                  <span className="group-hover:translate-x-1 transition-transform">→</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Additional Info Section */}
        {token && (
          <div className="mt-16 rounded-2xl border border-white/10 bg-white/[0.02] p-8">
            <h2 className="text-2xl font-bold text-white mb-4">Your Progress</h2>
            <p className="text-white/60">
              Track your applications, save your progress, and manage your documents across all services — all in one place.
            </p>
          </div>
        )}
      </div>

      {/* Login CTA */}
      {!token && (
        <div className="">
          <div className="content-wrap py-12 text-center">
            <h2 className="text-2xl font-bold text-white mb-4">Sign In to Save Your Progress</h2>
            <p className="text-white/60 mb-8 max-w-lg mx-auto">
              Create an account to track your applications, save checklists, and manage all your documents in one place.
            </p>
            <button
              onClick={() => navigate('/login')}
              className="inline-flex items-center gap-2 rounded-lg bg-[#f5c26b] px-8 py-3 font-medium text-slate-900 hover:bg-[#ffd966] transition-colors"
            >
              Sign In Now
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
