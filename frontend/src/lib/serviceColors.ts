/**
 * Per-service colour themes shared by the Hub cards and their ServiceArt illustrations.
 *
 * Each service is keyed to how its real document/ID is recognised (GST portal blue,
 * FSSAI food-green, Startup India saffron, navy passport…) so every card takes on its
 * own hue — the card tint/border/glow and the illustration both read from here.
 */

export type Hub = 'legal-id' | 'property' | 'business'

export type ServicePalette = { accent: string; accent2: string; tint: string; echo: string }

/* hex "#rrggbb" → "r,g,b" (for composing rgba() with variable alpha in CSS/SVG). */
export function hexRgb(hex: string): string {
  const n = parseInt(hex.slice(1), 16)
  return `${(n >> 16) & 255},${(n >> 8) & 255},${n & 255}`
}

export function hexA(hex: string, a: number): string {
  return `rgba(${hexRgb(hex)},${a})`
}

const HUB_DEFAULT: Record<Hub, { accent: string; accent2: string }> = {
  'legal-id': { accent: '#7dd3fc', accent2: '#3b82f6' },
  property: { accent: '#34d399', accent2: '#10b981' },
  business: { accent: '#fbbf24', accent2: '#fb923c' },
}

export const SERVICE_COLORS: Record<string, { accent: string; accent2: string }> = {
  // Legal ID
  'legal-id/aadhaar': { accent: '#fca55d', accent2: '#f43f5e' }, // saffron → red (UIDAI)
  'legal-id/pan': { accent: '#60a5fa', accent2: '#2563eb' }, // blue PAN card
  'legal-id/driving_licence': { accent: '#34d399', accent2: '#14b8a6' }, // teal-green
  'legal-id/passport': { accent: '#a5b4fc', accent2: '#4f46e5' }, // navy-indigo booklet
  'legal-id/voter_id': { accent: '#c084fc', accent2: '#9333ea' }, // violet EPIC
  'legal-id/certificates': { accent: '#fbbf24', accent2: '#f59e0b' }, // gold seal
  // Property
  'property/sale': { accent: '#34d399', accent2: '#f5c26b' }, // green + gold (money)
  'property/rental': { accent: '#22d3ee', accent2: '#0ea5e9' }, // cyan key
  'property/mutation': { accent: '#a78bfa', accent2: '#7c3aed' }, // violet transfer
  'property/encumbrance': { accent: '#60a5fa', accent2: '#4f46e5' }, // indigo search
  'property/index_ii': { accent: '#2dd4bf', accent2: '#0d9488' }, // teal register
  'property/registration': { accent: '#fb7185', accent2: '#e11d48' }, // red stamp
  'property/7/12': { accent: '#4ade80', accent2: '#16a34a' }, // land green
  'property/ferfar': { accent: '#f5c26b', accent2: '#d97706' }, // earth/amber map
  // Business
  'business/gst': { accent: '#60a5fa', accent2: '#2563eb' }, // GST portal blue
  'business/fssai': { accent: '#4ade80', accent2: '#16a34a' }, // food-safety green
  'business/msme': { accent: '#e879f9', accent2: '#c026d3' }, // Udyam magenta
  'business/shop_establishment': { accent: '#fb923c', accent2: '#ea580c' }, // shop orange
  'business/iec': { accent: '#22d3ee', accent2: '#0891b2' }, // trade cyan
  'business/trade_license': { accent: '#fbbf24', accent2: '#d97706' }, // amber licence
  'business/professional_tax': { accent: '#34d399', accent2: '#059669' }, // emerald (tax)
  'business/pan_tan': { accent: '#38bdf8', accent2: '#0284c7' }, // sky blue
  'business/startup_india': { accent: '#fb923c', accent2: '#f43f5e' }, // saffron → rose
}

function colorsFor(hub: Hub, key: string) {
  return SERVICE_COLORS[`${hub}/${key}`] || HUB_DEFAULT[hub]
}

/** Build a full illustration palette (tint/echo derived) from two accent colours.
 * Alphas kept low so the surfaces read as muted frosted glass, not neon. */
export function makePalette(accent: string, accent2: string): ServicePalette {
  return { accent, accent2, tint: hexA(accent2, 0.2), echo: hexA(accent, 0.24) }
}

/** Full palette (accent + accent2 + derived tint/echo) used by the SVG illustration. */
export function paletteFor(hub: Hub, key: string): ServicePalette {
  const c = colorsFor(hub, key)
  return makePalette(c.accent, c.accent2)
}

/** "r,g,b" pair for tinting the card surface/border/glow via the `--card-rgb` CSS var. */
export function cardRgb(hub: Hub, key: string): string {
  return hexRgb(colorsFor(hub, key).accent)
}

/* ── Service-category themes (the six hub/overview cards + the "all" tile) ─── */

export type Category = 'legal-id' | 'property' | 'business' | 'tracker' | 'documents' | 'chat' | 'all'

export const CATEGORY_COLORS: Record<Category, { accent: string; accent2: string }> = {
  'legal-id': { accent: '#60a5fa', accent2: '#2563eb' }, // blue
  property: { accent: '#34d399', accent2: '#10b981' }, // green
  business: { accent: '#fb923c', accent2: '#ea580c' }, // orange
  tracker: { accent: '#f472b6', accent2: '#db2777' }, // pink
  documents: { accent: '#a78bfa', accent2: '#7c3aed' }, // purple
  chat: { accent: '#22d3ee', accent2: '#0891b2' }, // cyan
  all: { accent: '#f5c26b', accent2: '#d97706' }, // gold
}

export function categoryPalette(cat: Category): ServicePalette {
  const c = CATEGORY_COLORS[cat] || CATEGORY_COLORS.all
  return makePalette(c.accent, c.accent2)
}

export function categoryRgb(cat: Category): string {
  return hexRgb((CATEGORY_COLORS[cat] || CATEGORY_COLORS.all).accent)
}
