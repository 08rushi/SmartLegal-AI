import type { TFunction } from 'i18next'
import { useTranslation } from 'react-i18next'
import type { UseVoiceAsk } from '../../hooks/useVoiceAsk'
import { formatTime } from '../../utils/recorder'

/** One line saying what the voice flow is doing, so state is never shown by colour alone. */
export function voiceStatusText(voice: UseVoiceAsk, t: TFunction): string {
  const { state, recorder, source } = voice
  const recording = state.status === 'recording'
  const permission = recorder.phase === 'asking' && recording
  const serverRecording = recording && source === 'server' && !permission
  if (permission) return t('status.permission')
  if (recording) return serverRecording ? t('status.recording', { time: formatTime(recorder.secondsLeft) }) : t('status.recordingBrowser')
  if (state.status === 'transcribing') return t('status.transcribing')
  if (state.status === 'asking') return t('status.asking')
  if (state.status === 'speaking') return t('status.speaking')
  if (state.status === 'error') return t('status.error')
  return t('status.idle')
}

/**
 * Mic button beside the text input: 🎤 to start, ⏹ to stop (press again). Same size/gold style as the Send button.
 */
export function VoiceButton({ voice }: { voice: UseVoiceAsk }) {
  const { t } = useTranslation('voice')
  const { state, micDisabled } = voice
  const recording = state.status === 'recording'
  const working = state.status === 'transcribing' || state.status === 'asking'
  const aria = recording ? t('button.ariaStop') : working ? t('button.ariaBusy') : t('button.ariaStart')

  return (
    <button
      type="button"
      onClick={voice.toggleMic}
      disabled={micDisabled}
      aria-label={aria}
      aria-pressed={recording}
      title={aria}
      className={`flex h-[46px] w-[46px] shrink-0 items-center justify-center rounded-2xl border text-lg transition-all disabled:cursor-not-allowed disabled:opacity-50 sm:h-[52px] sm:w-[52px] ${
        recording
          ? 'animate-pulse border-rose-500 bg-rose-500/20 text-rose-400 shadow-lg shadow-rose-500/20'
          : 'border-[#f5c26b]/30 bg-[#f5c26b]/10 text-[#f5c26b] hover:border-[#f5c26b]/60 hover:bg-[#f5c26b]/15'
      }`}
    >
      <span aria-hidden="true">{recording ? '⏹' : '🎤'}</span>
    </button>
  )
}

export default VoiceButton
