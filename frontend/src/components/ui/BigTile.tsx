import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Icon, type IconName } from './Icon'
import { SpeakButton } from './SpeakButton'

interface BigTileProps {
  icon: IconName
  /** The one short word/phrase shown on the tile (already translated). */
  label: string
  /** Navigate on click (router link). Use `onClick` instead for actions. */
  to?: string
  onClick?: () => void
  /** Show a speaker button that reads `speakText ?? label` aloud. Default true. */
  speaker?: boolean
  speakText?: string
  onSpeak?: () => void
  /** Optional extra line under the label. */
  hint?: ReactNode
  className?: string
}

/**
 * Icon-first glass tile for first-time / low-literacy users: icon + word (+ optional speaker). The tile body and
 * the speaker are separate controls (never nested), each its own control.
 */
export function BigTile({ icon, label, to, onClick, speaker = true, speakText, onSpeak, hint, className = '' }: BigTileProps) {
  const body = (
    <>
      <span className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04] text-accent">
        <Icon name={icon} size={32} />
      </span>
      <span className="block text-lg font-semibold leading-snug text-white">{label}</span>
      {hint && <span className="block text-sm text-fg-muted">{hint}</span>}
    </>
  )
  const bodyCls =
    'section-card hover-lift flex min-h-[132px] w-full flex-col items-start justify-center gap-3 rounded-[28px] p-5 pr-14 text-left'

  return (
    <div className={`relative ${className}`}>
      {to ? (
        <Link to={to} className={bodyCls}>
          {body}
        </Link>
      ) : (
        <button type="button" onClick={onClick} className={bodyCls}>
          {body}
        </button>
      )}
      {speaker && <SpeakButton text={speakText ?? label} label={label} onSpeak={onSpeak} className="absolute right-3 top-3" />}
    </div>
  )
}

export default BigTile
