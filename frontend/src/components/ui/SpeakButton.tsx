import { useTranslation } from 'react-i18next'
import { useSpeech } from '../../hooks/useSpeech'
import { Icon } from './Icon'

interface SpeakButtonProps {
  /** The text to read aloud (markdown/emoji/URLs are stripped automatically). */
  text: string
  /** Short visible name of what is being read, used in the aria-label ("Listen: {{label}}"). Defaults to `text`. */
  label?: string
  /** Called after the user starts speech (e.g. to reveal a SpeechNotice). */
  onSpeak?: () => void
  className?: string
}

/**
 * Small glass speaker button (🔊 / ⏹). Tap to listen, tap again to stop. Renders nothing when the browser has no
 * speech support (the text is still on screen). Only one speech plays app-wide.
 */
export function SpeakButton({ text, label, onSpeak, className = '' }: SpeakButtonProps) {
  const { t } = useTranslation('speech')
  const { speak, stop, speakingKey, isSupported } = useSpeech()
  if (!isSupported) return null
  const key = `btn:${text}`
  const active = speakingKey === key
  const name = label ?? text
  const aria = active ? t('stopListening') : t('listenTo', { label: name })

  return (
    <button
      type="button"
      aria-label={aria}
      title={aria}
      aria-pressed={active}
      onClick={() => {
        if (active) stop()
        else {
          speak(text, { key })
          onSpeak?.()
        }
      }}
      className={`inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border transition-all ${
        active
          ? 'border-[#f5c26b]/60 bg-[#f5c26b]/20 text-[#f5c26b]'
          : 'border-white/10 bg-white/5 text-slate-200 hover:border-[#f5c26b]/30 hover:bg-white/10'
      } ${className}`}
    >
      <Icon name={active ? 'stop' : 'speaker'} size={20} />
    </button>
  )
}

export default SpeakButton
