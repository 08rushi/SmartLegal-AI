/**
 * Pure state machine for the voice conversation (unit tested in src/tests/voice.test.mjs).
 *
 *   idle -> recording -> transcribing -> asking -> speaking -> idle      (error can follow any step)
 *
 * No imports / no TS-only runtime syntax: the node test runner imports this file directly.
 */

export type VoiceStatus = 'idle' | 'recording' | 'transcribing' | 'asking' | 'speaking' | 'error'

export type VoiceErrorCode =
  | 'denied'
  | 'noMic'
  | 'busyMic'
  | 'unsupported'
  | 'insecure'
  | 'tooShort'
  | 'tooBig'
  | 'badAudio'
  | 'noSpeech'
  | 'serverBusy'
  | 'serviceDown'
  | 'signIn'
  | 'network'
  | 'askFailed'
  | 'unknown'

export interface VoiceState {
  status: VoiceStatus
  /** What we heard (or the user typed / edited) for the current exchange. */
  heard: string
  /** Language detected by the server for `heard` (mr|hi|en) or null. */
  heardLang: string | null
  /** The latest answer text (kept after speaking so it can be replayed). */
  answer: string
  error: VoiceErrorCode | null
  /** Server-provided (already localized) error text, when there is one. */
  errorDetail: string | null
}

export type VoiceEvent =
  | { type: 'START' }
  | { type: 'STOP' }
  | { type: 'CANCEL' }
  | { type: 'HEARD'; text: string; lang?: string | null }
  | { type: 'SUBMIT'; text: string }
  | { type: 'ANSWER'; text: string; speak: boolean }
  | { type: 'REPLAY' }
  | { type: 'SPEAK_END' }
  | { type: 'STOP_SPEAKING' }
  | { type: 'FAIL'; code: VoiceErrorCode; detail?: string | null }
  | { type: 'DISMISS_ERROR' }
  | { type: 'RESET' }

export const initialVoiceState: VoiceState = {
  status: 'idle',
  heard: '',
  heardLang: null,
  answer: '',
  error: null,
  errorDetail: null,
}

/** The mic button may be pressed (to start) only in these states. Stop is allowed while recording. */
export function canStart(status: VoiceStatus): boolean {
  return status === 'idle' || status === 'error' || status === 'speaking'
}

/** True while something is in flight and the mic must stay disabled (AI is working). */
export function isBusy(status: VoiceStatus): boolean {
  return status === 'transcribing' || status === 'asking'
}

export function voiceReducer(state: VoiceState, ev: VoiceEvent): VoiceState {
  switch (ev.type) {
    case 'START':
      if (!canStart(state.status)) return state
      return { ...state, status: 'recording', error: null, errorDetail: null }
    case 'STOP':
      return state.status === 'recording' ? { ...state, status: 'transcribing' } : state
    case 'CANCEL':
      if (state.status === 'recording' || state.status === 'transcribing' || state.status === 'asking') {
        return { ...state, status: 'idle', error: null, errorDetail: null }
      }
      return state
    case 'HEARD': {
      if (state.status !== 'transcribing' && state.status !== 'recording') return state
      const text = ev.text.trim()
      if (!text) return { ...state, status: 'error', error: 'noSpeech', errorDetail: null }
      return { ...state, status: 'asking', heard: text, heardLang: ev.lang ?? null, answer: '', error: null, errorDetail: null }
    }
    case 'SUBMIT': {
      // typed or edited text; not allowed while recording or while the AI is already working
      if (state.status === 'recording' || isBusy(state.status)) return state
      const text = ev.text.trim()
      if (!text) return state
      return { ...state, status: 'asking', heard: text, answer: '', error: null, errorDetail: null }
    }
    case 'ANSWER':
      if (state.status !== 'asking') return state
      return { ...state, status: ev.speak ? 'speaking' : 'idle', answer: ev.text }
    case 'REPLAY':
      if (state.status === 'idle' && state.answer) return { ...state, status: 'speaking' }
      return state
    case 'SPEAK_END':
    case 'STOP_SPEAKING':
      return state.status === 'speaking' ? { ...state, status: 'idle' } : state
    case 'FAIL':
      return { ...state, status: 'error', error: ev.code, errorDetail: ev.detail ?? null }
    case 'DISMISS_ERROR':
      return state.status === 'error' ? { ...state, status: 'idle', error: null, errorDetail: null } : state
    case 'RESET':
      return initialVoiceState
    default:
      return state
  }
}

/** HTTP status of /voice/transcribe -> error code. */
export function errorCodeForStatus(status: number | null | undefined): VoiceErrorCode {
  if (status === 400) return 'badAudio'
  if (status === 401 || status === 403) return 'signIn'
  if (status === 413) return 'tooBig'
  if (status === 422) return 'noSpeech'
  if (status === 429) return 'serverBusy'
  if (status === 502 || status === 503 || status === 504) return 'serviceDown'
  if (status == null) return 'network'
  return 'unknown'
}
