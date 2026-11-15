import { useCallback, useEffect, useRef, useState } from 'react'
import {
  MAX_BYTES,
  MAX_SECONDS,
  MIN_MS,
  classifyMicError,
  detectSupport,
  remainingSeconds,
  ringProgress,
  startRecording,
  type ActiveRecording,
  type MicIssue,
  type RecordingResult,
} from '../utils/recorder'

/**
 * Microphone phase shown to the user:
 *  idle | asking (permission prompt open) | recording | denied | noMic | busy | unsupported | insecure | error
 */
export type RecorderPhase = 'idle' | 'asking' | 'recording' | MicIssue | 'error'

export interface UseVoiceRecorderOptions {
  maxSeconds?: number
  maxBytes?: number
  /** Called when a recording ends (by the user, the 60 s limit or the size guard). Too-short taps are dropped. */
  onComplete: (r: RecordingResult) => void
  onTooShort?: () => void
}

export interface UseVoiceRecorder {
  phase: RecorderPhase
  isRecording: boolean
  /** Why recording is impossible on this device/page (null = possible). */
  unavailable: 'unsupported' | 'insecure' | null
  secondsLeft: number
  /** 0..1 of the time limit used. */
  progress: number
  /** 0..1 loudness. */
  level: number
  start: () => Promise<void>
  stop: () => Promise<void>
  cancel: () => void
}

/** getUserMedia + MediaRecorder with permission states, a countdown, a level meter and cleanup on unmount. */
export function useVoiceRecorder(opts: UseVoiceRecorderOptions): UseVoiceRecorder {
  const maxSeconds = opts.maxSeconds ?? MAX_SECONDS
  const maxBytes = opts.maxBytes ?? MAX_BYTES
  const [phase, setPhase] = useState<RecorderPhase>('idle')
  const [elapsed, setElapsed] = useState(0)
  const [level, setLevel] = useState(0)
  const active = useRef<ActiveRecording | null>(null)
  const token = useRef(0)
  const optsRef = useRef(opts)
  optsRef.current = opts
  const unavailable = detectSupport()

  const deliver = useCallback((r: RecordingResult) => {
    active.current = null
    setPhase('idle')
    setElapsed(0)
    if (r.durationMs < MIN_MS || r.blob.size === 0) optsRef.current.onTooShort?.()
    else optsRef.current.onComplete(r)
  }, [])

  const start = useCallback(async () => {
    if (active.current) return
    const why = detectSupport()
    if (why) {
      setPhase(why)
      return
    }
    setPhase('asking')
    const mine = ++token.current
    try {
      const rec = await startRecording(
        { onLevel: setLevel, onTick: setElapsed, onAutoStop: deliver },
        { maxSeconds, maxBytes },
      )
      if (mine !== token.current) {
        rec.cancel() // cancelled (or unmounted) while the permission prompt was open
        return
      }
      active.current = rec
      setElapsed(0)
      setPhase('recording')
    } catch (e) {
      if (mine !== token.current) return
      active.current = null
      const issue = classifyMicError(e)
      setPhase(issue === 'unknown' ? 'error' : issue)
    }
  }, [deliver, maxSeconds, maxBytes])

  const stop = useCallback(async () => {
    const rec = active.current
    if (!rec) return
    const r = await rec.stop()
    deliver(r)
  }, [deliver])

  const cancel = useCallback(() => {
    token.current++
    active.current?.cancel()
    active.current = null
    setPhase('idle')
    setElapsed(0)
    setLevel(0)
  }, [])

  // release the microphone if the page is left mid-recording
  useEffect(
    () => () => {
      token.current++
      active.current?.cancel()
      active.current = null
    },
    [],
  )

  return {
    phase,
    isRecording: phase === 'recording',
    unavailable,
    secondsLeft: remainingSeconds(elapsed, maxSeconds),
    progress: ringProgress(elapsed, maxSeconds),
    level,
    start,
    stop,
    cancel,
  }
}
