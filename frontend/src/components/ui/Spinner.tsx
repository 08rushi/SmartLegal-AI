import { useTranslation } from 'react-i18next'

interface SpinnerProps {
  /** Pixel size. Default 28. */
  size?: number
  /** Screen-reader text. Defaults to "Loading...". Pass `visibleLabel` to also show it. */
  label?: string
  visibleLabel?: boolean
  className?: string
}

/** Loading indicator. Rotation is disabled under prefers-reduced-motion (the ring is still visible). */
export function Spinner({ size = 28, label, visibleLabel = false, className = '' }: SpinnerProps) {
  const { t } = useTranslation('ui')
  const text = label ?? t('loading')
  return (
    <span role="status" className={`inline-flex items-center gap-3 text-slate-300 ${className}`}>
      <span
        aria-hidden="true"
        style={{ width: size, height: size }}
        className="inline-block animate-spin rounded-full border-[3px] border-white/15 border-t-[#f5c26b]"
      />
      <span className={visibleLabel ? '' : 'sr-only'}>{text}</span>
    </span>
  )
}

export default Spinner
