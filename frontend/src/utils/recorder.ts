/**
 * Microphone recording helpers. Pure parts (unit tested in src/tests/voice.test.mjs): pickMime, extensionForMime,
 * formatTime, remainingSeconds, ringProgress, levelFromBytes, classifyMicError, chooseSttSource, checkSupport.
 * Runtime part: startRecording (getUserMedia + MediaRecorder + level meter).
 *
 * Keep this file free of imports and TypeScript-only runtime syntax: the node test runner imports it directly.
 * Recordings live only in memory (a Blob handed to the caller); nothing is stored.
 */

export const MAX_SECONDS = 60
export const MAX_BYTES = 10 * 1024 * 1024
/** Shorter than this is treated as an accidental tap. */
export const MIN_MS = 600

/** Best first. Safari only does mp4/aac. */
export const MIME_CANDIDATES = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus'] as const

/** First candidate the browser supports, or '' (let the browser choose). */
export function pickMime(isTypeSupported: ((m: string) => boolean) | null | undefined): string {
  if (typeof isTypeSupported !== 'function') return ''
  for (const m of MIME_CANDIDATES) {
    try {
      if (isTypeSupported(m)) return m
    } catch {
      /* ignore */
    }
  }
  return ''
}

/** File extension for the upload so the server can sniff the container. */
export function extensionForMime(mime: string | null | undefined): string {
  const m = String(mime ?? '').toLowerCase()
  if (m.includes('mp4') || m.includes('aac')) return 'm4a'
  if (m.includes('ogg')) return 'ogg'
  if (m.includes('wav')) return 'wav'
  return 'webm'
}

/** 75 -> "1:15", 5 -> "0:05". Negative/NaN -> "0:00". */
export function formatTime(seconds: number): string {
  const s = Number.isFinite(seconds) && seconds > 0 ? Math.floor(seconds) : 0
  const m = Math.floor(s / 60)
  return `${m}:${String(s % 60).padStart(2, '0')}`
}

/** Whole seconds left on the countdown (rounded up so it shows 0 only at the very end). */
export function remainingSeconds(elapsedMs: number, max: number = MAX_SECONDS): number {
  const left = max - (Number.isFinite(elapsedMs) ? elapsedMs : 0) / 1000
  return Math.max(0, Math.min(max, Math.ceil(left)))
}

/** 0..1 fraction of the time limit used (for the countdown ring). */
export function ringProgress(elapsedMs: number, max: number = MAX_SECONDS): number {
  if (!(max > 0)) return 1
  const f = (Number.isFinite(elapsedMs) ? elapsedMs : 0) / 1000 / max
  return Math.max(0, Math.min(1, f))
}

/** Loudness 0..1 from time-domain bytes (128 = silence), boosted so normal speech fills the meter. */
export function levelFromBytes(data: ArrayLike<number>): number {
  const n = data.length
  if (!n) return 0
  let sum = 0
  for (let i = 0; i < n; i++) {
    const v = (data[i] - 128) / 128
    sum += v * v
  }
  const rms = Math.sqrt(sum / n)
  return Math.max(0, Math.min(1, rms * 3.2))
}

export type MicIssue = 'denied' | 'noMic' | 'unsupported' | 'insecure' | 'busy' | 'unknown'

/** Maps a getUserMedia / MediaRecorder error to a state the UI can explain. */
export function classifyMicError(err: unknown): MicIssue {
  const name = String((err as { name?: string } | null)?.name ?? '')
  if (name === 'NotAllowedError' || name === 'PermissionDeniedError' || name === 'SecurityError') return 'denied'
  if (name === 'NotFoundError' || name === 'DevicesNotFoundError' || name === 'OverconstrainedError') return 'noMic'
  if (name === 'NotReadableError' || name === 'TrackStartError' || name === 'AbortError') return 'busy'
  if (name === 'TypeError' || name === 'NotSupportedError') return 'unsupported'
  return 'unknown'
}

export interface SupportEnv {
  isSecureContext?: boolean
  hasGetUserMedia?: boolean
  hasMediaRecorder?: boolean
}

/** null when recording can work, otherwise why not. getUserMedia needs https (localhost counts as secure). */
export function checkSupport(env: SupportEnv): 'insecure' | 'unsupported' | null {
  if (env.isSecureContext === false) return 'insecure'
  if (!env.hasGetUserMedia || !env.hasMediaRecorder) return 'unsupported'
  return null
}

export type SttSource = 'server' | 'browser' | 'none'

/** Server Whisper first (when the server offers it and we can record), else the browser engine, else typing. */
export function chooseSttSource(opts: { serverStt: boolean; canRecord: boolean; hasBrowserRecognition: boolean }): SttSource {
  if (opts.serverStt && opts.canRecord) return 'server'
  if (opts.hasBrowserRecognition) return 'browser'
  return 'none'
}

// ---------------------------------------------------------------------------------------------
// Runtime
// ---------------------------------------------------------------------------------------------

export function detectSupport(): 'insecure' | 'unsupported' | null {
  const g: any = typeof globalThis !== 'undefined' ? globalThis : {}
  return checkSupport({
    isSecureContext: g.isSecureContext,
    hasGetUserMedia: !!g.navigator?.mediaDevices?.getUserMedia,
    hasMediaRecorder: typeof g.MediaRecorder === 'function',
  })
}

export interface RecordingResult {
  blob: Blob
  mime: string
  durationMs: number
  /** Why recording ended. */
  reason: 'user' | 'limit' | 'size'
}

export interface RecorderHandlers {
  onLevel?: (level: number) => void
  onTick?: (elapsedMs: number) => void
}

export interface ActiveRecording {
  /** Stops and resolves with the audio. */
  stop(): Promise<RecordingResult>
  /** Stops and throws the audio away. */
  cancel(): void
}

/**
 * Asks for the microphone and starts recording. Rejects with the original getUserMedia error (use
 * classifyMicError). Hard-stops at maxSeconds or maxBytes; `onAutoStop` fires with the result then.
 * All tracks and the audio context are released when it ends.
 */
export async function startRecording(
  handlers: RecorderHandlers & { onAutoStop?: (r: RecordingResult) => void },
  limits: { maxSeconds?: number; maxBytes?: number } = {},
): Promise<ActiveRecording> {
  const g: any = globalThis
  const maxMs = (limits.maxSeconds ?? MAX_SECONDS) * 1000
  const maxBytes = limits.maxBytes ?? MAX_BYTES
  const stream: MediaStream = await g.navigator.mediaDevices.getUserMedia({
    audio: { echoCancellation: true, noiseSuppression: true },
  })

  const mime = pickMime((m) => g.MediaRecorder.isTypeSupported?.(m))
  let rec: MediaRecorder
  try {
    rec = mime ? new g.MediaRecorder(stream, { mimeType: mime }) : new g.MediaRecorder(stream)
  } catch (e) {
    stream.getTracks().forEach((t) => t.stop())
    throw e
  }

  const chunks: Blob[] = []
  let bytes = 0
  const startedAt = Date.now()
  let discarded = false
  let ended: RecordingResult['reason'] | null = null
  let settle: ((r: RecordingResult) => void) | null = null
  let result: RecordingResult | null = null

  // level meter (optional: skipped quietly if AudioContext is unavailable)
  let audioCtx: AudioContext | null = null
  let raf = 0
  let timer: ReturnType<typeof setInterval> | null = null
  try {
    const Ctx = g.AudioContext || g.webkitAudioContext
    if (Ctx && handlers.onLevel) {
      audioCtx = new Ctx()
      const analyser = audioCtx!.createAnalyser()
      analyser.fftSize = 512
      audioCtx!.createMediaStreamSource(stream).connect(analyser)
      const buf = new Uint8Array(analyser.fftSize)
      const loop = () => {
        analyser.getByteTimeDomainData(buf)
        handlers.onLevel?.(levelFromBytes(buf))
        raf = requestAnimationFrame(loop)
      }
      raf = requestAnimationFrame(loop)
    }
  } catch {
    audioCtx = null
  }

  const release = () => {
    if (timer) clearInterval(timer)
    timer = null
    if (raf) cancelAnimationFrame(raf)
    raf = 0
    stream.getTracks().forEach((t) => t.stop())
    try {
      void audioCtx?.close()
    } catch {
      /* ignore */
    }
    audioCtx = null
    handlers.onLevel?.(0)
  }

  rec.ondataavailable = (e: BlobEvent) => {
    if (!e.data || !e.data.size) return
    chunks.push(e.data)
    bytes += e.data.size
    if (bytes >= maxBytes) finish('size')
  }
  rec.onstop = () => {
    release()
    if (discarded) return
    result = {
      blob: new Blob(chunks, { type: rec.mimeType || mime || 'audio/webm' }),
      mime: rec.mimeType || mime || 'audio/webm',
      durationMs: Date.now() - startedAt,
      reason: ended ?? 'user',
    }
    if (settle) settle(result)
    else if (ended && ended !== 'user') handlers.onAutoStop?.(result)
  }

  function finish(reason: RecordingResult['reason']) {
    if (ended) return
    ended = reason
    try {
      if (rec.state !== 'inactive') rec.stop()
    } catch {
      release()
    }
  }

  rec.start(1000) // 1 s slices so the size guard can act while recording
  timer = setInterval(() => {
    const elapsed = Date.now() - startedAt
    handlers.onTick?.(elapsed)
    if (elapsed >= maxMs) finish('limit')
  }, 200)

  return {
    stop() {
      return new Promise<RecordingResult>((resolve) => {
        if (result) return resolve(result)
        settle = resolve
        if (!ended) ended = 'user'
        try {
          if (rec.state !== 'inactive') rec.stop()
          else release()
        } catch {
          release()
        }
      })
    },
    cancel() {
      discarded = true
      ended = ended ?? 'user'
      try {
        if (rec.state !== 'inactive') rec.stop()
        else release()
      } catch {
        release()
      }
      chunks.length = 0
    },
  }
}
