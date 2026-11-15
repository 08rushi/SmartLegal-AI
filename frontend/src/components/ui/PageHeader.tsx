import type { ReactNode } from 'react'
import { Icon, type IconName } from './Icon'
import { SpeakButton } from './SpeakButton'

interface PageHeaderProps {
  /** The page <h1>. Use exactly one PageHeader per page. */
  title: string
  subtitle?: string
  icon?: IconName
  /** Show a speaker that reads title + subtitle aloud. */
  speaker?: boolean
  /** Right-aligned actions (buttons). */
  actions?: ReactNode
  className?: string
}

/** Page title block: optional icon, h1, short subtitle, optional speaker and actions. */
export function PageHeader({ title, subtitle, icon, speaker = false, actions, className = '' }: PageHeaderProps) {
  return (
    <header className={`flex flex-wrap items-start justify-between gap-4 ${className}`}>
      <div className="flex min-w-0 items-start gap-4">
        {icon && (
          <span className="brand-mark !h-12 !w-12 shrink-0 text-accent">
            <Icon name={icon} size={26} />
          </span>
        )}
        <div className="min-w-0">
          <h1 className="text-3xl font-semibold text-white sm:text-4xl">{title}</h1>
          {subtitle && <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">{subtitle}</p>}
        </div>
      </div>
      <div className="flex items-center gap-3">
        {speaker && <SpeakButton text={subtitle ? `${title}. ${subtitle}` : title} label={title} />}
        {actions}
      </div>
    </header>
  )
}

export default PageHeader
