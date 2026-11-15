import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { normalizeLanguage } from '../i18n/languages'
import { createSpeechController, type SpeechController, type SpeechState, type VoiceMatch } from '../utils/speech'

/**
 * Text-to-speech hook (window.speechSynthesis). One shared controller for the whole app so two buttons
 * never talk over each other.
 *
 *   const { speak, stop, isSpeaking, isSupported, voice, notice } = useSpeech()
 *   speak('Hello')                       // reads aloud in the active app language
 *   speak(text, { key: 'tile-upload' })  // key lets a button know it is the one speaking (speakingKey)
 *   stop()
 *
 * `voice` says which voice/language is really used; show `notice` (see components/ui/SpeechNotice) when it is
 * not an exact match. Never throws: when speech is unsupported, speak() is a no-op and isSupported is false.
 */

let shared: SpeechController | null = null
function getController(): SpeechController {
  if (!shared) shared = createSpeechController()
  return shared
}

export interface UseSpeechVoice {
  /** BCP-47 tag of the voice used, e.g. "hi-IN". */
  language: string
  name: string
  /** BCP-47 tag asked for, e.g. "mr-IN". */
  requested: string
  match: VoiceMatch
}

export interface UseSpeech {
  speak: (text: string, opts?: { lang?: string; key?: string; onEnd?: () => void }) => void
  stop: () => void
  isSpeaking: boolean
  /** The key of the speech in progress (or null). */
  speakingKey: string | null
  isSupported: boolean
  /** False until the browser has loaded its voice list (Chrome loads it late). */
  voicesReady: boolean
  /** null when no voice is installed or speech is unsupported. */
  voice: UseSpeechVoice | null
  /** null = all good. Otherwise show a message: unsupported | noVoice | hindiVoice | englishVoice. */
  notice: SpeechState['notice']
}

export function useSpeech(): UseSpeech {
  const { i18n } = useTranslation()
  const lang = normalizeLanguage(i18n.resolvedLanguage || i18n.language) ?? 'en'
  const ctrl = getController()
  const [state, setState] = useState<SpeechState>(() => ctrl.getState())

  useEffect(() => {
    ctrl.setLanguage(lang)
    setState(ctrl.getState())
    return ctrl.subscribe(() => setState(ctrl.getState()))
  }, [ctrl, lang])

  const speak = useCallback<UseSpeech['speak']>((text, opts) => ctrl.speak(text, { lang, ...opts }), [ctrl, lang])
  const stop = useCallback(() => ctrl.stop(), [ctrl])

  const c = state.choice
  return {
    speak,
    stop,
    isSpeaking: state.isSpeaking,
    speakingKey: state.activeKey,
    isSupported: state.isSupported,
    voicesReady: state.voicesReady,
    voice: c ? { language: c.language, name: c.voice.name, requested: c.requested, match: c.match } : null,
    notice: state.notice,
  }
}

export default useSpeech
