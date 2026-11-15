import { apiClient } from './api'
import { extensionForMime } from '../utils/recorder'

export interface VoiceCapabilities {
  stt: boolean
  languages: string[]
  max_seconds: number
  max_bytes: number
}

export interface TranscribeResult {
  text: string
  language: string
  duration_seconds: number
}

export const FALLBACK_CAPABILITIES: VoiceCapabilities = {
  stt: false,
  languages: ['mr', 'hi', 'en'],
  max_seconds: 60,
  max_bytes: 10485760,
}

export async function fetchVoiceCapabilities(signal?: AbortSignal): Promise<VoiceCapabilities> {
  const res = await apiClient.get<VoiceCapabilities>('/voice/capabilities', { signal })
  return { ...FALLBACK_CAPABILITIES, ...res.data }
}

/** Sends one recording (multipart field `audio`) to the transcribe route. The audio goes nowhere else. */
export async function transcribeAudio(
  blob: Blob,
  mime: string,
  language: string | undefined,
  signal?: AbortSignal,
): Promise<TranscribeResult> {
  const form = new FormData()
  form.append('audio', blob, `voice.${extensionForMime(mime)}`)
  if (language) form.append('language', language)
  const res = await apiClient.post<TranscribeResult>('/voice/transcribe', form, {
    timeout: 60000,
    signal,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}
