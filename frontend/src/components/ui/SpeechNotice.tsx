import { useTranslation } from 'react-i18next'
import { useSpeech } from '../../hooks/useSpeech'
import { Notice } from './Notice'

/**
 * Tells the user when the voice is not an exact match ("A Hindi voice is being used.") or speech is not
 * available. Renders nothing when everything is fine, or while `show` is false (e.g. before first speak).
 */
export function SpeechNotice({ show = true, className = '' }: { show?: boolean; className?: string }) {
  const { t } = useTranslation('speech')
  const { notice, voicesReady } = useSpeech()
  if (!show || !notice) return null
  if (notice === 'noVoice' && !voicesReady) return null // voices still loading
  return (
    <Notice tone="info" className={className}>
      {t(`notice.${notice}`)}
    </Notice>
  )
}

export default SpeechNotice
