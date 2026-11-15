import type { ElementType, HTMLAttributes, ReactNode } from 'react'

export interface UiCardProps extends HTMLAttributes<HTMLElement> {
  /** Element to render (div, section, article, li ...). Default div. */
  as?: ElementType
  /** `default` glass panel, `raised` muted glass, `accent` outlined in gold. */
  tone?: 'default' | 'raised' | 'accent'
  /** Inner padding. Default true. */
  padded?: boolean
  children?: ReactNode
}

const TONE = {
  default: 'glass-panel',
  raised: 'panel-muted',
  accent: 'glass-panel !border-[rgba(245,194,107,0.3)]',
} as const

/** Glass content container (same look as the original section-card). */
export function UiCard({ as: Tag = 'div', tone = 'default', padded = true, className = '', children, ...rest }: UiCardProps) {
  return (
    <Tag className={`rounded-[28px] ${TONE[tone]} ${padded ? 'p-5 sm:p-6' : ''} ${className}`} {...rest}>
      {children}
    </Tag>
  )
}

export default UiCard
