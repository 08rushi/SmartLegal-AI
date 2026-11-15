import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { Icon, type IconName } from './Icon'

export type NoticeTone = 'info' | 'success' | 'warn' | 'error'

interface NoticeProps {
  tone?: NoticeTone
  /** Bold heading. Defaults to a one-word label for the tone ("Note", "Done", "Careful", "Problem"). */
  title?: string
  children?: ReactNode
  /** If given, shows a Close button. */
  onClose?: () => void
  className?: string
}

const CONFIG: Record<NoticeTone, { cls: string; icon: IconName }> = {
  info: { cls: 'border-info-line bg-info-bg text-info', icon: 'info' },
  success: { cls: 'border-ok-line bg-ok-bg text-ok', icon: 'check' },
  warn: { cls: 'border-warn-line bg-warn-bg text-warn', icon: 'warning' },
  error: { cls: 'border-danger-line bg-danger-bg text-danger', icon: 'error' },
}

/** Message box: coloured border + icon + word + text. Errors use role="alert", others role="status". */
export function Notice({ tone = 'info', title, children, onClose, className = '' }: NoticeProps) {
  const { t } = useTranslation('ui')
  const { cls, icon } = CONFIG[tone]
  return (
    <div role={tone === 'error' ? 'alert' : 'status'} className={`flex items-start gap-3 rounded-[22px] border p-4 ${cls} ${className}`}>
      <Icon name={icon} size={22} className="mt-0.5" />
      <div className="min-w-0 flex-1">
        <p className="font-semibold">{title ?? t(`notice.${tone}`)}</p>
        {children && <div className="mt-1 text-sm text-slate-200">{children}</div>}
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          aria-label={t('close')}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-slate-300 hover:bg-white/10 hover:text-white"
        >
          <Icon name="close" size={18} />
        </button>
      )}
    </div>
  )
}

export default Notice
