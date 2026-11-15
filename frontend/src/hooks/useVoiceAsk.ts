import { useCallback, useEffect, useReducer, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { normalizeLanguage } from '../i18n/languages'
import { fetchVoiceCapabilities, transcribeAudio, type VoiceCapabilities } from '../services/voiceApi'
import { chooseSttSource, detectSupport, type RecordingResult, type SttSource } from '../utils/recorder'
import { toBcp47 } from '../utils/speech'
import { errorCodeForStatus, initialVoiceState, voiceReducer, type VoiceErrorCode, type VoiceState } from '../utils/voiceMachine'
import { useSpeech } from './useSpeech'
import { useVoiceRecorder, type UseVoiceRecorder } from './useVoiceRecorder'

const AUTO_SPEAK_KEY = 'sl_voice_autospeak'
const SPEAK_KEY = 'voice-answer'

function readAutoSpeak(): boolean {
  try {
    return localStorage.getItem(AUTO_SPEAK_KEY) !== '0'
  } catch {
    return true
  }
}

let capsPromise: Promise<VoiceCapabilities | null> | null = null
function loadCapabilities(): Promise<VoiceCapabilities | null> {
  if (!capsPromise) {
    capsPromise = fetchVoiceCapabilities().catch(() => {
      capsPromise = null // allow a retry next time
      return null
    })
  }
  return capsPromise
}

function browserRecognitionCtor(): any {
  const g: any = typeof window !== 'undefined' ? window : {}
  return g.SpeechRecognition || g.webkitSpeechRecognition || null
}

export interface UseVoiceAskOptions {
  /** The page's question handler. Resolve with the plain answer text; reject on failure. Honour `signal` if you can. */
  ask: (text: string, signal: AbortSignal) => Promise<string>
  /** True while the page is busy answering something else (typed question): the mic is disabled. */
  disabled?: boolean
}

export interface UseVoiceAsk {
  state: VoiceState
  /** Where speech-to-text comes from on this device (null until capabilities are known). */
  source: SttSource | null
  recorder: UseVoiceRecorder
  /** Mic button is not usable right now. */
  micDisabled: boolean
  autoSpeak: boolean
  setAutoSpeak: (on: boolean) => void
  speechSupported: boolean
  /** Press once to start, again to stop. */
  toggleMic: () => void
  cancel: () => void
  /** Ask with typed or edited text. */
  submitText: (text: string) => void
  replay: () => void
  stopSpeaking: () => void
  dismissError: () => void
}

/**
 * Voice question flow: record -> transcribe -> ask(text) -> speak the answer.
 * Speech-to-text: server Whisper if capabilities.stt, else the browser's SpeechRecognition, else typing only.
 * Recordings stay in memory and go only to /voice/transcribe.
 */
export function useVoiceAsk({ ask, disabled = false }: UseVoiceAskOptions): UseVoiceAsk {
  const { i18n } = useTranslation()
  const lang = normalizeLanguage(i18n.resolvedLanguage || i18n.language) ?? 'en'
  const [state, dispatch] = useReducer(voiceReducer, initialVoiceState)
  const [caps, setCaps] = useState<VoiceCapabilities | null>(null)
  const [capsLoaded, setCapsLoaded] = useState(false)
  const [autoSpeak, setAutoSpeakState] = useState<boolean>(readAutoSpeak)
  const speech = useSpeech()

  const stateRef = useRef(state)
  stateRef.current = state
  const askRef = useRef(ask)
  askRef.current = ask
  const langRef = useRef(lang)
  langRef.current = lang
  const autoSpeakRef = useRef(autoSpeak)
  autoSpeakRef.current = autoSpeak
  const netAbort = useRef<AbortController | null>(null)
  const recognition = useRef<any>(null)
  const gotText = useRef(false)

  useEffect(() => {
    let live = true
    loadCapabilities().then((c) => {
      if (!live) return
      setCaps(c)
      setCapsLoaded(true)
    })
    return () => {
      live = false
    }
  }, [])

  // ----- server transcription ------------------------------------------------------------
  const onRecorded = useCallback(async (r: RecordingResult) => {
    dispatch({ type: 'STOP' })
    const ctl = new AbortController()
    netAbort.current = ctl
    try {
      const res = await transcribeAudio(r.blob, r.mime, langRef.current, ctl.signal)
      if (ctl.signal.aborted) return
      dispatch({ type: 'HEARD', text: res.text ?? '', lang: res.language })
    } catch (e: any) {
      if (ctl.signal.aborted) return
      const status: number | null = e?.response?.status ?? null
      const detail = e?.response?.data?.detail
      dispatch({ type: 'FAIL', code: errorCodeForStatus(status), detail: typeof detail === 'string' ? detail : null })
    }
  }, [])

  const recorder = useVoiceRecorder({
    maxSeconds: caps?.max_seconds,
    maxBytes: caps?.max_bytes,
    onComplete: onRecorded,
    onTooShort: () => dispatch({ type: 'FAIL', code: 'tooShort' }),
  })

  // microphone problems (permission prompt result) -> error state
  useEffect(() => {
    if (state.status !== 'recording') return
    const map: Partial<Record<string, VoiceErrorCode>> = {
      denied: 'denied',
      noMic: 'noMic',
      busy: 'busyMic',
      unsupported: 'unsupported',
      insecure: 'insecure',
      error: 'unknown',
    }
    const code = map[recorder.phase]
    if (code && stateRef.current.status === 'recording' && sourceRef.current === 'server') dispatch({ type: 'FAIL', code })
  }, [recorder.phase, state.status])

  // ----- source selection ----------------------------------------------------------------
  const hasBrowser = !!browserRecognitionCtor()
  const source: SttSource | null = capsLoaded
    ? chooseSttSource({ serverStt: !!caps?.stt, canRecord: recorder.unavailable === null, hasBrowserRecognition: hasBrowser })
    : null
  const sourceRef = useRef<SttSource | null>(source)
  sourceRef.current = source

  // ----- browser recognition fallback ----------------------------------------------------
  const startBrowser = useCallback(() => {
    const Ctor = browserRecognitionCtor()
    if (!Ctor) {
      dispatch({ type: 'FAIL', code: 'unsupported' })
      return
    }
    gotText.current = false
    try {
      const rec = new Ctor()
      rec.continuous = false
      rec.interimResults = false
      rec.lang = toBcp47(langRef.current)
      rec.onresult = (ev: any) => {
        const text = ev?.results?.[0]?.[0]?.transcript
        if (text) {
          gotText.current = true
          dispatch({ type: 'HEARD', text: String(text), lang: langRef.current })
        }
      }
      rec.onerror = (ev: any) => {
        const err = ev?.error
        const code: VoiceErrorCode =
          err === 'not-allowed' || err === 'service-not-allowed'
            ? 'denied'
            : err === 'audio-capture'
              ? 'noMic'
              : err === 'network'
                ? 'network'
                : err === 'no-speech'
                  ? 'noSpeech'
                  : 'unknown'
        if (err === 'aborted') return
        gotText.current = true // error already reported
        dispatch({ type: 'FAIL', code })
      }
      rec.onend = () => {
        recognition.current = null
        const s = stateRef.current.status
        if (!gotText.current && (s === 'recording' || s === 'transcribing')) dispatch({ type: 'FAIL', code: 'noSpeech' })
      }
      recognition.current = rec
      rec.start()
    } catch {
      recognition.current = null
      dispatch({ type: 'FAIL', code: 'unsupported' })
    }
  }, [])

  const stopBrowser = useCallback((abort: boolean) => {
    const rec = recognition.current
    if (!rec) return
    try {
      if (abort) {
        rec.onend = null
        rec.onresult = null
        rec.onerror = null
        rec.abort()
        recognition.current = null
      } else rec.stop()
    } catch {
      /* ignore */
    }
  }, [])

  // ----- actions -------------------------------------------------------------------------
  const startListening = useCallback(async () => {
    speech.stop()
    recorder.cancel() // clears a stale "denied" phase from the previous attempt
    dispatch({ type: 'START' })
    let src = sourceRef.current
    if (src === null) {
      const c = await loadCapabilities()
      setCaps(c)
      setCapsLoaded(true)
      src = chooseSttSource({
        serverStt: !!c?.stt,
        canRecord: detectSupport() === null,
        hasBrowserRecognition: !!browserRecognitionCtor(),
      })
      sourceRef.current = src
    }
    if (src === 'server') await recorder.start()
    else if (src === 'browser') startBrowser()
    else dispatch({ type: 'FAIL', code: detectSupport() === 'insecure' ? 'insecure' : 'unsupported' })
  }, [recorder, speech, startBrowser])

  const toggleMic = useCallback(() => {
    const st = stateRef.current.status
    if (st === 'recording') {
      if (sourceRef.current === 'server') void recorder.stop()
      else {
        dispatch({ type: 'STOP' })
        stopBrowser(false)
      }
    } else if (st === 'idle' || st === 'error' || st === 'speaking') {
      void startListening()
    }
  }, [recorder, startListening, stopBrowser])

  const cancel = useCallback(() => {
    netAbort.current?.abort()
    netAbort.current = null
    recorder.cancel()
    stopBrowser(true)
    if (stateRef.current.status === 'speaking') speech.stop()
    dispatch({ type: stateRef.current.status === 'speaking' ? 'STOP_SPEAKING' : 'CANCEL' })
  }, [recorder, speech, stopBrowser])

  const submitText = useCallback((text: string) => {
    speech.stop()
    dispatch({ type: 'SUBMIT', text })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const stopSpeaking = useCallback(() => {
    speech.stop()
    dispatch({ type: 'STOP_SPEAKING' })
  }, [speech])

  const replay = useCallback(() => dispatch({ type: 'REPLAY' }), [])
  const dismissError = useCallback(() => dispatch({ type: 'DISMISS_ERROR' }), [])

  const setAutoSpeak = useCallback((on: boolean) => {
    setAutoSpeakState(on)
    try {
      localStorage.setItem(AUTO_SPEAK_KEY, on ? '1' : '0')
    } catch {
      /* ignore */
    }
    if (!on) {
      speech.stop()
      dispatch({ type: 'STOP_SPEAKING' })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ----- ask when the machine enters "asking" ---------------------------------------------
  useEffect(() => {
    if (state.status !== 'asking') return
    const ctl = new AbortController()
    netAbort.current = ctl
    askRef
      .current(state.heard, ctl.signal)
      .then((text) => {
        if (ctl.signal.aborted) return
        dispatch({ type: 'ANSWER', text: String(text ?? ''), speak: autoSpeakRef.current && speech.isSupported })
      })
      .catch((e: unknown) => {
        if (ctl.signal.aborted) return
        dispatch({ type: 'FAIL', code: 'askFailed', detail: typeof e === 'string' ? e : null })
      })
    return () => ctl.abort()
    // run once per submitted question
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.status === 'asking' ? state.heard : null, state.status === 'asking'])

  // ----- speak the answer when the machine enters "speaking" -------------------------------
  const spokeStarted = useRef(false)
  useEffect(() => {
    if (state.status !== 'speaking') {
      spokeStarted.current = false
      return
    }
    spokeStarted.current = false
    speech.speak(state.answer, { key: SPEAK_KEY, onEnd: () => dispatch({ type: 'SPEAK_END' }) })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.status === 'speaking', state.answer])

  // someone else (another speaker button) took over the voice: leave the speaking state
  useEffect(() => {
    if (state.status !== 'speaking') return
    if (speech.speakingKey === SPEAK_KEY) spokeStarted.current = true
    else if (spokeStarted.current) dispatch({ type: 'SPEAK_END' })
  }, [state.status, speech.speakingKey])

  // ----- cleanup on unmount / navigation ---------------------------------------------------
  useEffect(
    () => () => {
      netAbort.current?.abort()
      stopBrowser(true)
      if (stateRef.current.status === 'speaking') speech.stop()
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  )

  const micDisabled = disabled || state.status === 'transcribing' || state.status === 'asking'

  return {
    state,
    source,
    recorder,
    micDisabled,
    autoSpeak,
    setAutoSpeak,
    speechSupported: speech.isSupported,
    toggleMic,
    cancel,
    submitText,
    replay,
    stopSpeaking,
    dismissError,
  }
}
