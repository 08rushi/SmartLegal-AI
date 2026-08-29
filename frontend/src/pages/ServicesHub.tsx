import { useNavigate } from 'react-router-dom'
import { useAppSelector } from '../hooks/redux'
import CategoryArt from '../components/CategoryArt'
import { Card } from '../components/Card'

interface ServiceCard {
  key: string
  title: string
  description: string
  icon: string
  iconLabel: string
  route: string
  badge?: string
  color: 'blue' | 'purple' | 'green' | 'orange' | 'pink'
  art: 'legal-id' | 'property' | 'business' | 'tracker' | 'documents' | 'chat'
}

const services: ServiceCard[] = [
  {
    key: 'legal-id',
    title: 'Legal ID Hub',
    description: 'Government ID guidance — Aadhaar, PAN, Passport, Driving License, Voter ID & Certificates',
    icon: 'ID',
    iconLabel: 'Legal ID services',
    route: '/legal-id',
    color: 'blue',
    badge: 'Popular',
    art: 'legal-id'
  },
  {
    key: 'property',
    title: 'Property Hub',
    description: 'Property transaction guidance — Sale, Rental, Mutation, Registration & Encumbrance Certificate',
    icon: 'PR',
    iconLabel: 'Property services',
    route: '/property-hub',
    color: 'green',
    badge: 'Popular',
    art: 'property'
  },
  {
    key: 'business',
    title: 'Business License Hub',
    description: 'Business registration guidance - GST, FSSAI, MSME, Shop Act, IEC, Trade License & Startup India',
    icon: 'BIZ',
    iconLabel: 'Business license services',
    route: '/business-hub',
    color: 'orange',
    badge: 'New',
    art: 'business'
  },
  {
    key: 'tracker',
    title: 'Service Tracker',
    description: 'Track applications, save checklists, set reminders, and enable browser notifications',
    icon: '4D',
    iconLabel: 'Service tracker',
    route: '/tracker',
    color: 'pink',
    badge: '4D',
    art: 'tracker'
  },
  {
    key: 'documents',
    title: 'Document Analysis',
    description: 'Upload and analyze legal documents — Get risk assessments and plain-language explanations',
    icon: 'DOC',
    iconLabel: 'Document analysis',
    route: '/upload',
    color: 'purple',
    art: 'documents'
  },
  {
    key: 'chat',
    title: 'AI Legal Assistant',
    description: 'Ask questions about your documents — Get instant answers and clause clarifications',
    icon: 'AI',
    iconLabel: 'AI legal assistant',
    route: '/chat',
    color: 'orange',
    art: 'chat'
  }
]

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
    <div className="content-wrap py-5 sm:py-6">
      <Card variant="section" className="mx-auto max-w-7xl rounded-[32px] p-6 sm:p-8">
        {/* ─ Hero Section ─ */}
        <div>
          <div>
            <span className="section-eyebrow">Government Services</span>
            <h1 className="text-4xl font-bold text-white mt-4">
              Online Service Center
            </h1>
            <p className="text-sm mt-3 text-white/60">
              Complete legal guidance for Indians — from government IDs to property transactions to document analysis
            </p>
          </div>
          <div className="flex flex-wrap gap-3 text-sm mt-4">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs">
              <span>✓</span> Expert Guidance
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs">
              <span>✓</span> Hindi & English
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs">
              <span>✓</span> AI-Powered
            </span>
          </div>
        </div>

        {/* Services Grid */}
        <div className="py-10">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {services.map((service) => (
              <Card
                key={service.key}
                variant="section"
                hoverLift
                onClick={() => navigate(service.route)}
                className="group hub-service-card relative overflow-hidden rounded-2xl p-8 cursor-pointer"
              >
                <div className="hub-service-card__art" aria-hidden="true">
                  <CategoryArt art={service.art} className="hub-service-svg" />
                </div>

                <div className="relative z-10 space-y-4">
                  {/* Icon & Badge */}
                  <div className="flex items-start justify-between">
                    <span className="service-icon-badge" aria-label={service.iconLabel}>
                      {service.icon}
                    </span>
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
              </Card>
            ))}
          </div>

          {/* Additional Info Section */}
          {token && (
            <Card variant="outline" className="mt-16 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">Your Progress</h2>
              <p className="text-white/60">
                Track your applications, save your progress, and manage your documents across all services — all in one place.
              </p>
            </Card>
          )}
        </div>

        {/* Login CTA */}
        {!token && (
          <Card variant="outline" className="mt-6 rounded-2xl p-8 text-center">
            <h2 className="text-2xl font-bold text-white mb-4">Sign In to Save Your Progress</h2>
            <p className="text-white/60 mb-8 max-w-lg mx-auto">
              Create an account to track your applications, save checklists, and manage all your documents in one place.
            </p>
            <button
              onClick={() => navigate('/login')}
              className="btn-primary inline-flex items-center gap-2 px-8 py-3"
            >
              Sign In Now
            </button>
          </Card>
        )}
      </Card>
    </div>
  )
}
