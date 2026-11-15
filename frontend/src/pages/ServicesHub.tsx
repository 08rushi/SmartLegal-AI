import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAppSelector } from '../hooks/redux'
import CategoryArt from '../components/CategoryArt'
import { Card } from '../components/Card'

interface ServiceCard {
  key: string
  /** Key under hubs:services.cards.<i18nKey> (title, description, iconLabel). */
  i18nKey: 'legalId' | 'property' | 'business' | 'tracker' | 'documents' | 'chat'
  icon: string
  route: string
  /** Key under hubs:services.badge.<badge>, or a literal symbol such as "4D". */
  badge?: 'popular' | 'new' | '4D'
  color: 'blue' | 'purple' | 'green' | 'orange' | 'pink'
  art: 'legal-id' | 'property' | 'business' | 'tracker' | 'documents' | 'chat'
}

const services: ServiceCard[] = [
  {
    key: 'legal-id',
    i18nKey: 'legalId',
    icon: 'ID',
    route: '/legal-id',
    color: 'blue',
    badge: 'popular',
    art: 'legal-id'
  },
  {
    key: 'property',
    i18nKey: 'property',
    icon: 'PR',
    route: '/property-hub',
    color: 'green',
    badge: 'popular',
    art: 'property'
  },
  {
    key: 'business',
    i18nKey: 'business',
    icon: 'BIZ',
    route: '/business-hub',
    color: 'orange',
    badge: 'new',
    art: 'business'
  },
  {
    key: 'tracker',
    i18nKey: 'tracker',
    icon: '4D',
    route: '/tracker',
    color: 'pink',
    badge: '4D',
    art: 'tracker'
  },
  {
    key: 'documents',
    i18nKey: 'documents',
    icon: 'DOC',
    route: '/upload',
    color: 'purple',
    art: 'documents'
  },
  {
    key: 'chat',
    i18nKey: 'chat',
    icon: 'AI',
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
  const { t } = useTranslation('hubs')
  const { isAuthenticated } = useAppSelector((state) => state.auth)

  return (
    <div className="content-wrap py-5 sm:py-6">
      <Card variant="section" className="mx-auto max-w-7xl rounded-[32px] p-6 sm:p-8">
        {/* ─ Hero Section ─ */}
        <div>
          <div>
            <span className="section-eyebrow">{t('services.eyebrow')}</span>
            <h1 className="text-4xl font-bold text-white mt-4">
              {t('services.title')}
            </h1>
            <p className="text-sm mt-3 text-white/60">
              {t('services.subtitle')}
            </p>
          </div>
          <div className="flex flex-wrap gap-3 text-sm mt-4">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs">
              <span>✓</span> {t('services.chips.expert')}
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs">
              <span>✓</span> {t('services.chips.languages')}
            </span>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs">
              <span>✓</span> {t('services.chips.ai')}
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
                    <span className="service-icon-badge" aria-label={t(`services.cards.${service.i18nKey}.iconLabel`)}>
                      {service.icon}
                    </span>
                    {service.badge && (
                      <span className={`inline-block rounded-full px-3 py-1 text-xs font-semibold border ${badgeColorMap[service.color]}`}>
                        {service.badge === '4D' ? service.badge : t(`services.badge.${service.badge}`)}
                      </span>
                    )}
                  </div>

                  {/* Title & Description */}
                  <div>
                    <h3 className="text-2xl font-bold text-white group-hover:text-white transition-colors">
                      {t(`services.cards.${service.i18nKey}.title`)}
                    </h3>
                    <p className="mt-3 text-sm text-white/60 leading-relaxed">
                      {t(`services.cards.${service.i18nKey}.description`)}
                    </p>
                  </div>

                  {/* CTA */}
                  <div className="flex items-center gap-2 text-sm font-medium text-white/70 group-hover:text-white transition-colors pt-4">
                    <span>{t('services.explore')}</span>
                    <span className="group-hover:translate-x-1 transition-transform">→</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Additional Info Section */}
          {isAuthenticated && (
            <Card variant="outline" className="mt-16 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">{t('services.progress.title')}</h2>
              <p className="text-white/60">
                {t('services.progress.body')}
              </p>
            </Card>
          )}
        </div>

        {/* Login CTA */}
        {!isAuthenticated && (
          <Card variant="outline" className="mt-6 rounded-2xl p-8 text-center">
            <h2 className="text-2xl font-bold text-white mb-4">{t('services.signIn.title')}</h2>
            <p className="text-white/60 mb-8 max-w-lg mx-auto">
              {t('services.signIn.body')}
            </p>
            <button
              onClick={() => navigate('/login')}
              className="btn-primary inline-flex items-center gap-2 px-8 py-3"
            >
              {t('services.signIn.cta')}
            </button>
          </Card>
        )}
      </Card>
    </div>
  )
}
