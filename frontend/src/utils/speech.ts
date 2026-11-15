/**
 * Text-to-speech helpers built on window.speechSynthesis. Framework-free and safe to import anywhere.
 *
 * Pure parts (unit tested in src/tests/speech.test.mjs): toBcp47, stripForSpeech, chunkText, pickVoice.
 * Runtime part: createSpeechController (used by hooks/useSpeech.ts). It never throws when speech is
 * unsupported; calls simply do nothing and report isSupported = false.
 *
 * Keep this file free of imports and TypeScript-only runtime syntax (enums, parameter properties): the
 * node test runner imports it directly.
 */

export type SpeechLang = 'en' | 'hi' | 'mr'

/** App language -> BCP-47 tag used for the utterance / voice lookup. */
export const BCP47: Record<SpeechLang, string> = {
  en: 'en-IN',
  hi: 'hi-IN',
  mr: 'mr-IN',
}

/** Maps an app language code (or any tag like "hi-IN", "mr") to a BCP-47 tag. Unknown -> en-IN. */
export function toBcp47(lang: string | null | undefined): string {
  const base = String(lang ?? '').toLowerCase().split(/[-_]/)[0]
  return (BCP47 as Record<string, string>)[base] ?? BCP47.en
}

/** Primary language subtag ("hi-IN" -> "hi"). */
function primary(tag: string): string {
  return String(tag ?? '').toLowerCase().split(/[-_]/)[0]
}

// ---------------------------------------------------------------------------------------------
// Text cleaning
// ---------------------------------------------------------------------------------------------

const EMOJI = /[\p{Extended_Pictographic}\p{Emoji_Presentation}‍︎️⃣]/gu
const URL_RE = /\b(?:https?:\/\/|www\.)[^\s)]+/gi

/**
 * Removes markdown syntax, emoji and URLs so the engine reads only words.
 * Line breaks become sentence breaks so headings and list items are not run together.
 */
export function stripForSpeech(input: string | null | undefined): string {
  let s = String(input ?? '')
  s = s.replace(/\r\n?/g, '\n')
  s = s.replace(/```[\s\S]*?```/g, ' ') // fenced code
  s = s.replace(/<[^>\n]+>/g, ' ') // html tags
  s = s.replace(/!\[[^\]]*\]\([^)]*\)/g, ' ') // images
  s = s.replace(/\[([^\]]+)\]\([^)]*\)/g, '$1') // links -> label
  s = s.replace(URL_RE, ' ')
  s = s.replace(/`([^`]*)`/g, '$1') // inline code
  s = s.replace(/^\s{0,3}#{1,6}\s+/gm, '') // headings
  s = s.replace(/^\s{0,3}>\s?/gm, '') // blockquote
  s = s.replace(/^\s*[-*+•]\s+/gm, '') // bullets
  s = s.replace(/^\s*\d+[.)]\s+/gm, '') // numbered list markers
  s = s.replace(/^\s*[-*_=]{3,}\s*$/gm, ' ') // rules
  s = s.replace(/^\s*\|?[\s:|-]{3,}\|?\s*$/gm, ' ') // table separator rows
  s = s.replace(/\|/g, ', ') // table cells
  s = s.replace(/(\*\*|__)(.*?)\1/g, '$2') // bold
  s = s.replace(/(\*|_)(.*?)\1/g, '$2') // italic
  s = s.replace(/~~(.*?)~~/g, '$1')
  s = s.replace(/[*_~`#>]+/g, ' ') // stray markers
  s = s.replace(EMOJI, ' ')
  // newline -> sentence break (unless the line already ends with punctuation)
  s = s
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => (/[.!?।॥:;,]$/.test(line) ? line : `${line}.`))
    .join(' ')
  s = s.replace(/\s+([.,!?;:।॥])/g, '$1')
  s = s.replace(/\s+/g, ' ').trim()
  return s
}

// ---------------------------------------------------------------------------------------------
// Chunking
// ---------------------------------------------------------------------------------------------

/** Default max chunk length. Some engines (notably Chrome network voices) cut off past ~200-300 chars. */
export const DEFAULT_CHUNK_SIZE = 200

function splitLong(sentence: string, max: number): string[] {
  const out: string[] = []
  let rest = sentence.trim()
  while (rest.length > max) {
    // prefer a clause break, then a space, near the limit
    let cut = -1
    for (const re of [/[,;:،]\s/g, /\s/g]) {
      let m: RegExpExecArray | null
      let last = -1
      re.lastIndex = 0
      while ((m = re.exec(rest)) && m.index < max) last = m.index + m[0].length
      if (last > max * 0.4) {
        cut = last
        break
      }
    }
    if (cut <= 0) cut = max // no break found: hard cut
    out.push(rest.slice(0, cut).trim())
    rest = rest.slice(cut).trim()
  }
  if (rest) out.push(rest)
  return out
}

/**
 * Splits text at sentence boundaries (. ! ? । ॥) into chunks of at most `max` characters.
 * Short sentences are packed together; a sentence longer than `max` is split at commas / spaces.
 */
export function chunkText(text: string, max: number = DEFAULT_CHUNK_SIZE): string[] {
  const clean = String(text ?? '').replace(/\s+/g, ' ').trim()
  if (!clean) return []
  const limit = Math.max(20, max)
  const sentences = clean.match(/[^.!?।॥]+(?:[.!?।॥]+|$)/g) ?? [clean]
  const chunks: string[] = []
  let cur = ''
  for (const raw of sentences) {
    const sentence = raw.trim()
    if (!sentence) continue
    const parts = sentence.length > limit ? splitLong(sentence, limit) : [sentence]
    for (const part of parts) {
      if (!cur) cur = part
      else if (cur.length + 1 + part.length <= limit) cur += ` ${part}`
      else {
        chunks.push(cur)
        cur = part
      }
    }
  }
  if (cur) chunks.push(cur)
  return chunks
}

// ---------------------------------------------------------------------------------------------
// Voice selection
// ---------------------------------------------------------------------------------------------

export interface VoiceLike {
  lang: string
  name: string
  localService?: boolean
  default?: boolean
}

/** How the chosen voice relates to the requested language. */
export type VoiceMatch = 'exact' | 'fallback-hi' | 'fallback-en'

export interface VoiceChoice<V extends VoiceLike = VoiceLike> {
  voice: V
  /** BCP-47 tag of the voice actually used (e.g. "hi-IN"). */
  language: string
  /** BCP-47 tag that was asked for (e.g. "mr-IN"). */
  requested: string
  match: VoiceMatch
}

const QUALITY_HINT = /natural|neural|online|enhanced|premium|google/i

function scoreVoice(v: VoiceLike, wantTag: string): number {
  let score = 0
  if (String(v.lang).replace('_', '-').toLowerCase() === wantTag.toLowerCase()) score += 10
  if (QUALITY_HINT.test(v.name)) score += 3
  if (v.localService) score += 1 // works offline
  if (v.default) score += 0.5
  return score
}

function best<V extends VoiceLike>(voices: V[], lang: string, wantTag: string): V | null {
  const pool = voices.filter((v) => primary(v.lang) === lang)
  if (!pool.length) return null
  return pool.reduce((a, b) => (scoreVoice(b, wantTag) > scoreVoice(a, wantTag) ? b : a))
}

/**
 * Picks the best installed voice. Order: exact language (mr -> mr voice), then for Marathi a Hindi voice
 * (Devanagari is read acceptably), then English. Returns null when no voice is installed at all.
 * `match` lets the UI show a notice such as "Hindi voice used".
 */
export function pickVoice<V extends VoiceLike>(voices: V[], appLang: string): VoiceChoice<V> | null {
  const list = Array.isArray(voices) ? voices : []
  const requested = toBcp47(appLang)
  const lang = primary(requested)

  const exact = best(list, lang, requested)
  if (exact) return { voice: exact, language: exact.lang, requested, match: 'exact' }

  if (lang === 'mr') {
    const hi = best(list, 'hi', BCP47.hi)
    if (hi) return { voice: hi, language: hi.lang, requested, match: 'fallback-hi' }
  }

  const en = best(list, 'en', BCP47.en)
  if (en) return { voice: en, language: en.lang, requested, match: 'fallback-en' }

  return null
}

/** Notice code for the UI (map to a translated string): none when the voice matches the language. */
export function noticeFor(choice: VoiceChoice | null, supported: boolean): 'unsupported' | 'noVoice' | 'hindiVoice' | 'englishVoice' | null {
  if (!supported) return 'unsupported'
  if (!choice) return 'noVoice'
  if (choice.match === 'fallback-hi') return 'hindiVoice'
  if (choice.match === 'fallback-en') return 'englishVoice'
  return null
}

// ---------------------------------------------------------------------------------------------
// Runtime controller
// ---------------------------------------------------------------------------------------------

interface SynthLike {
  speak(u: unknown): void
  cancel(): void
  pause?(): void
  resume?(): void
  getVoices(): VoiceLike[]
  speaking?: boolean
  paused?: boolean
  addEventListener?(type: string, fn: () => void): void
  removeEventListener?(type: string, fn: () => void): void
}

export interface SpeechState {
  isSupported: boolean
  isSpeaking: boolean
  /** The `key` passed to speak() for the current speech (lets one button show "speaking" for itself only). */
  activeKey: string | null
  /** True once the browser has reported its voice list (voiceschanged or immediately available). */
  voicesReady: boolean
  /** Voice used for the current/last language, or null if none is installed. */
  choice: VoiceChoice | null
  notice: ReturnType<typeof noticeFor>
}

export interface SpeechController {
  speak(text: string, opts?: { lang?: string; key?: string; onEnd?: () => void }): void
  stop(): void
  getState(): SpeechState
  setLanguage(lang: string): void
  subscribe(fn: () => void): () => void
  destroy(): void
}

type UtteranceCtor = new (text: string) => {
  lang: string
  voice: unknown
  rate: number
  onend: (() => void) | null
  onerror: ((e: { error?: string }) => void) | null
  onstart?: (() => void) | null
}

/**
 * Creates a controller around a SpeechSynthesis-like object. Defaults to the browser globals and returns a
 * harmless no-op controller when they are missing.
 */
export function createSpeechController(
  synthArg?: SynthLike | null,
  UtteranceArg?: UtteranceCtor | null,
  initialLang: string = 'en',
): SpeechController {
  const g: any = typeof globalThis !== 'undefined' ? globalThis : {}
  const synth: SynthLike | null = synthArg !== undefined ? synthArg : (g.speechSynthesis ?? null)
  const Utterance: UtteranceCtor | null = UtteranceArg !== undefined ? UtteranceArg : (g.SpeechSynthesisUtterance ?? null)
  const supported = !!synth && !!Utterance

  let lang = initialLang
  let speaking = false
  let activeKey: string | null = null
  let voicesReady = false
  let choice: VoiceChoice | null = null
  let runId = 0
  let keepAlive: ReturnType<typeof setInterval> | null = null
  const alive: unknown[] = [] // hold references: some engines garbage-collect utterances mid-speech
  const listeners = new Set<() => void>()

  const emit = () => listeners.forEach((fn) => fn())

  const refreshVoices = () => {
    if (!supported) return
    try {
      const voices = synth!.getVoices() ?? []
      if (voices.length) voicesReady = true
      choice = pickVoice(voices, lang)
    } catch {
      choice = null
    }
    emit()
  }

  const onVoicesChanged = () => refreshVoices()
  if (supported) {
    try {
      synth!.addEventListener?.('voiceschanged', onVoicesChanged)
    } catch {
      /* ignore */
    }
    refreshVoices()
  }

  const clearKeepAlive = () => {
    if (keepAlive) clearInterval(keepAlive)
    keepAlive = null
  }

  const finish = (id: number, onEnd?: () => void) => {
    if (id !== runId) return
    speaking = false
    activeKey = null
    alive.length = 0
    clearKeepAlive()
    emit()
    onEnd?.()
  }

  return {
    speak(text, opts) {
      if (!supported) return
      try {
        const useLang = opts?.lang ?? lang
        if (useLang !== lang) {
          lang = useLang
          refreshVoices()
        } else if (!choice) {
          refreshVoices()
        }
        const chunks = chunkText(stripForSpeech(text))
        synth!.cancel()
        speaking = false
        alive.length = 0
        clearKeepAlive()
        const id = ++runId
        if (!chunks.length) {
          emit()
          opts?.onEnd?.()
          return
        }
        speaking = true
        activeKey = opts?.key ?? null
        emit()

        const speakChunk = (i: number) => {
          if (id !== runId) return
          if (i >= chunks.length) return finish(id, opts?.onEnd)
          const u = new Utterance!(chunks[i])
          u.lang = choice?.language ?? toBcp47(lang)
          if (choice) u.voice = choice.voice
          u.rate = 0.95 // slightly slower is easier to follow
          u.onend = () => speakChunk(i + 1)
          u.onerror = (e) => {
            // "canceled"/"interrupted" come from our own stop(); anything else ends the run
            if (id !== runId) return
            if (e?.error === 'canceled' || e?.error === 'interrupted') return
            finish(id, opts?.onEnd)
          }
          alive.push(u)
          if (synth!.paused) synth!.resume?.()
          synth!.speak(u)
        }
        // Chrome drops speak() issued in the same tick as cancel(); defer one tick.
        setTimeout(() => speakChunk(0), 0)

        // Chrome bug: long speech silently stalls after ~15s. Nudge the engine while speaking.
        keepAlive = setInterval(() => {
          if (id !== runId || !synth!.speaking) return
          try {
            synth!.pause?.()
            synth!.resume?.()
          } catch {
            /* ignore */
          }
        }, 10000)
      } catch {
        speaking = false
        activeKey = null
        emit()
      }
    },
    stop() {
      if (!supported) return
      runId++
      try {
        synth!.cancel()
      } catch {
        /* ignore */
      }
      speaking = false
      activeKey = null
      alive.length = 0
      clearKeepAlive()
      emit()
    },
    setLanguage(next) {
      if (next === lang) return
      lang = next
      refreshVoices()
    },
    getState() {
      return { isSupported: supported, isSpeaking: speaking, activeKey, voicesReady, choice, notice: noticeFor(choice, supported) }
    },
    subscribe(fn) {
      listeners.add(fn)
      return () => {
        listeners.delete(fn)
      }
    },
    destroy() {
      runId++
      clearKeepAlive()
      listeners.clear()
      try {
        synth?.removeEventListener?.('voiceschanged', onVoicesChanged)
        if (speaking) synth?.cancel()
      } catch {
        /* ignore */
      }
    },
  }
}
