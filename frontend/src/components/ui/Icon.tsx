import type { HTMLAttributes } from 'react'

/**
 * Icon set in the original SmartLegal look: emoji / text glyphs (like the previous nav's 📂, ⚖, ▾, →).
 * The API (name, size) is unchanged so every page keeps working. Icons are decorative (aria-hidden):
 * always put a text label or aria-label next to them.
 */
const GLYPHS = {
  home: '🏠',
  upload: '⬆️',
  ask: '💬',
  help: '🛠️',
  more: '⋯',
  menu: '☰',
  speaker: '🔊',
  stop: '⏹',
  check: '✅',
  warning: '⚠️',
  alert: '❗',
  info: 'ℹ️',
  error: '❌',
  close: '✕',
  document: '📄',
  schemes: '🏛️',
  services: '🗂️',
  folder: '📂',
  user: '👤',
  chevronDown: '▾',
  arrowRight: '→',
  back: '←',
  pin: '📍',
  scale: '⚖',
  logout: '↩',
  compare: '⇄',
  tracker: '📋',
  book: '📚',
  download: '⬇️',
  calendar: '📅',
  money: '💰',
  mic: '🎤',
} as const

export type IconName = keyof typeof GLYPHS

/** Name -> glyph map (exported for tests and for places that need the raw glyph, e.g. PDF/print). */
export const ICON_GLYPHS: Record<IconName, string> = GLYPHS

export interface IconProps extends Omit<HTMLAttributes<HTMLSpanElement>, 'children'> {
  name: IconName
  /** Box size in pixels (the glyph is ~80% of it). Default 24. */
  size?: number
}

export function Icon({ name, size = 24, className = '', style, ...rest }: IconProps) {
  return (
    <span
      aria-hidden="true"
      className={`inline-flex shrink-0 select-none items-center justify-center leading-none ${className}`}
      style={{ width: size, height: size, fontSize: Math.round(size * 0.8), ...style }}
      {...rest}
    >
      {GLYPHS[name]}
    </span>
  )
}

export default Icon
