/**
 * App navigation model (the original top navigation: five links, a Services dropdown and the Legal Advisor pill).
 * Pure data + helpers: no React, "erasable" TypeScript so node can unit-test it.
 * Labels are i18n keys (namespace:key), translated in Layout.
 */

export interface NavItem {
  to: string
  labelKey: string
}

/** The five plain links shown before the Services dropdown (desktop bar, mobile menu and footer). */
export const NAV_ITEMS: NavItem[] = [
  { to: '/', labelKey: 'nav:home' },
  { to: '/upload', labelKey: 'nav:upload' },
  { to: '/analysis', labelKey: 'nav:review' },
  { to: '/chat', labelKey: 'nav:askAi' },
  { to: '/knowledge-base', labelKey: 'nav:knowledgeBase' },
]

export type ServiceArt = 'legal-id' | 'property' | 'business' | 'tracker' | 'all'

export interface ServiceCard {
  key: string
  titleKey: string
  descriptionKey: string
  art: ServiceArt
  to: string
}

/** Entries of the Services dropdown. */
export const SERVICE_CARDS: ServiceCard[] = [
  { key: 'legal-id', titleKey: 'nav:serviceCards.legalId.title', descriptionKey: 'nav:serviceCards.legalId.description', art: 'legal-id', to: '/legal-id' },
  { key: 'property', titleKey: 'nav:serviceCards.property.title', descriptionKey: 'nav:serviceCards.property.description', art: 'property', to: '/property-hub' },
  { key: 'business', titleKey: 'nav:serviceCards.business.title', descriptionKey: 'nav:serviceCards.business.description', art: 'business', to: '/business-hub' },
  { key: 'yojana', titleKey: 'nav:serviceCards.yojana.title', descriptionKey: 'nav:serviceCards.yojana.description', art: 'all', to: '/yojana' },
  { key: 'tracker', titleKey: 'nav:serviceCards.tracker.title', descriptionKey: 'nav:serviceCards.tracker.description', art: 'tracker', to: '/tracker' },
  { key: 'all-services', titleKey: 'nav:serviceCards.all.title', descriptionKey: 'nav:serviceCards.all.description', art: 'all', to: '/services' },
]

/** Footer "Product" links after the five main links. */
export const FOOTER_EXTRA_LINKS: NavItem[] = [
  { to: '/legal-id', labelKey: 'footer:links.legalId' },
  { to: '/property-hub', labelKey: 'footer:links.property' },
  { to: '/business-hub', labelKey: 'footer:links.business' },
  { to: '/tracker', labelKey: 'footer:links.tracker' },
  { to: '/documents', labelKey: 'footer:links.documents' },
]

/** True when the current page belongs under the Services dropdown (lights the Services button). */
export function isServicesActive(pathname: string): boolean {
  return (
    pathname.includes('/legal-id') ||
    pathname.includes('/property') ||
    pathname.includes('/business') ||
    pathname === '/services' ||
    pathname === '/tracker'
  )
}
