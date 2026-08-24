import React, { ComponentPropsWithRef, ElementType, forwardRef } from 'react'

export type CardVariant = 'section' | 'hero' | 'info' | 'metric' | 'glass' | 'outline'

export interface CardProps<T extends ElementType = 'div'> {
  as?: T
  variant?: CardVariant
  hoverLift?: boolean
  glow?: boolean
  className?: string
  children?: React.ReactNode
}

const variantClasses: Record<CardVariant, string> = {
  section: 'section-card',
  hero: 'hero-card glow-ring',
  info: 'info-card',
  metric: 'metric-card',
  glass: 'glass-panel',
  outline: 'rounded-[28px] border border-white/10 bg-white/[0.02] backdrop-blur-xl',
}

/**
 * Universal Reusable Card Component for SmartLegal AI
 * Supports variant styling, smooth hover effects, custom HTML elements (div, article, section, etc.),
 * forwardRef, and semantic compound sub-components.
 */
export const CardInternal = forwardRef<HTMLElement, CardProps<ElementType> & ComponentPropsWithRef<ElementType>>(
  function CardInternal(
    {
      as,
      variant = 'section',
      hoverLift = false,
      glow = false,
      className = '',
      children,
      ...props
    },
    ref
  ) {
    const Component = as || 'div'

    const variantKey = (variant as CardVariant) in variantClasses ? (variant as CardVariant) : 'section'
    const selectedVariant = variantClasses[variantKey]
    const hoverClass = hoverLift ? 'hover-lift cursor-pointer' : ''
    const glowClass = glow ? 'ring-1 ring-[#8a5cff]/35 shadow-[0_0_45px_rgba(124,58,237,0.22)]' : ''

    const baseClass = `${selectedVariant} ${hoverClass} ${glowClass} ${className}`.trim()

    return (
      <Component ref={ref} className={baseClass} {...props}>
        {children}
      </Component>
    )
  }
)

// Sub-components
function CardHeader({ className = '', children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={`flex flex-col gap-1.5 ${className}`} {...props}>{children}</div>
}

function CardTitle({ className = '', children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={`text-xl font-semibold text-white ${className}`} {...props}>{children}</h3>
}

function CardDescription({ className = '', children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={`mt-2 text-sm leading-7 text-slate-400 ${className}`} {...props}>{children}</p>
}

function CardFooter({ className = '', children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={`mt-6 flex items-center justify-between text-sm ${className}`} {...props}>{children}</div>
}

function CardIcon({ className = '', children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-xl text-[#f5c26b] ${className}`} {...props}>
      {children}
    </div>
  )
}

export type CardComponent = typeof CardInternal & {
  Header: typeof CardHeader
  Title: typeof CardTitle
  Description: typeof CardDescription
  Footer: typeof CardFooter
  Icon: typeof CardIcon
}

export const Card = CardInternal as unknown as CardComponent

Card.Header = CardHeader
Card.Title = CardTitle
Card.Description = CardDescription
Card.Footer = CardFooter
Card.Icon = CardIcon

export default Card
