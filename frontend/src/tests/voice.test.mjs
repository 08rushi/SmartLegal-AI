/**
 * Voice helpers + state machine (plain node --test).
 */
import test from 'node:test'
import assert from 'node:assert/strict'
import {
  pickMime,
  extensionForMime,
  formatTime,
  remainingSeconds,
  ringProgress,
  levelFromBytes,
  classifyMicError,
  checkSupport,
  chooseSttSource,
  MAX_SECONDS,
} from '../utils/recorder.ts'
import { voiceReducer, initialVoiceState, errorCodeForStatus, canStart, isBusy } from '../utils/voiceMachine.ts'

test('pickMime prefers webm/opus then falls back to mp4 (Safari)', () => {
  assert.equal(pickMime(() => true), 'audio/webm;codecs=opus')
  assert.equal(pickMime((m) => m === 'audio/mp4'), 'audio/mp4')
  assert.equal(pickMime((m) => m === 'audio/webm'), 'audio/webm')
  assert.equal(pickMime(() => false), '')
  assert.equal(pickMime(undefined), '')
  assert.equal(
    pickMime(() => {
      throw new Error('x')
    }),
    '',
  )
})

test('extensionForMime', () => {
  assert.equal(extensionForMime('audio/mp4'), 'm4a')
  assert.equal(extensionForMime('audio/webm;codecs=opus'), 'webm')
  assert.equal(extensionForMime('audio/ogg;codecs=opus'), 'ogg')
  assert.equal(extensionForMime(''), 'webm')
})

test('formatTime and countdown', () => {
  assert.equal(formatTime(75), '1:15')
  assert.equal(formatTime(5), '0:05')
  assert.equal(formatTime(-3), '0:00')
  assert.equal(formatTime(NaN), '0:00')
  assert.equal(remainingSeconds(0), 60)
  assert.equal(remainingSeconds(100), 60)
  assert.equal(remainingSeconds(1500), 59)
  assert.equal(remainingSeconds(59_900), 1)
  assert.equal(remainingSeconds(60_000), 0)
  assert.equal(remainingSeconds(90_000), 0)
  assert.equal(ringProgress(30_000), 0.5)
  assert.equal(ringProgress(120_000), 1)
  assert.equal(ringProgress(-5), 0)
  assert.equal(MAX_SECONDS, 60)
})

test('levelFromBytes', () => {
  assert.equal(levelFromBytes(new Uint8Array(64).fill(128)), 0)
  assert.equal(levelFromBytes([]), 0)
  const loud = new Uint8Array(64).map((_, i) => (i % 2 ? 255 : 0))
  assert.equal(levelFromBytes(loud), 1)
})

test('classifyMicError', () => {
  assert.equal(classifyMicError({ name: 'NotAllowedError' }), 'denied')
  assert.equal(classifyMicError({ name: 'NotFoundError' }), 'noMic')
  assert.equal(classifyMicError({ name: 'NotReadableError' }), 'busy')
  assert.equal(classifyMicError({ name: 'TypeError' }), 'unsupported')
  assert.equal(classifyMicError(null), 'unknown')
})

test('checkSupport and chooseSttSource', () => {
  assert.equal(checkSupport({ isSecureContext: false, hasGetUserMedia: true, hasMediaRecorder: true }), 'insecure')
  assert.equal(checkSupport({ isSecureContext: true, hasGetUserMedia: false, hasMediaRecorder: true }), 'unsupported')
  assert.equal(checkSupport({ isSecureContext: true, hasGetUserMedia: true, hasMediaRecorder: true }), null)
  assert.equal(chooseSttSource({ serverStt: true, canRecord: true, hasBrowserRecognition: true }), 'server')
  assert.equal(chooseSttSource({ serverStt: false, canRecord: true, hasBrowserRecognition: true }), 'browser')
  assert.equal(chooseSttSource({ serverStt: true, canRecord: false, hasBrowserRecognition: true }), 'browser')
  assert.equal(chooseSttSource({ serverStt: false, canRecord: true, hasBrowserRecognition: false }), 'none')
})

const run = (events, from = initialVoiceState) => events.reduce(voiceReducer, from)

test('happy path: idle -> recording -> transcribing -> asking -> speaking -> idle', () => {
  let s = initialVoiceState
  s = voiceReducer(s, { type: 'START' })
  assert.equal(s.status, 'recording')
  s = voiceReducer(s, { type: 'STOP' })
  assert.equal(s.status, 'transcribing')
  s = voiceReducer(s, { type: 'HEARD', text: ' भाडे करार काय आहे? ', lang: 'mr' })
  assert.equal(s.status, 'asking')
  assert.equal(s.heard, 'भाडे करार काय आहे?')
  assert.equal(s.heardLang, 'mr')
  s = voiceReducer(s, { type: 'ANSWER', text: 'उत्तर', speak: true })
  assert.equal(s.status, 'speaking')
  assert.equal(s.answer, 'उत्तर')
  s = voiceReducer(s, { type: 'SPEAK_END' })
  assert.equal(s.status, 'idle')
  assert.equal(s.answer, 'उत्तर') // kept for replay
})

test('answer without auto-speak goes straight to idle; replay speaks again', () => {
  let s = run([
    { type: 'SUBMIT', text: 'hi' },
    { type: 'ANSWER', text: 'ok', speak: false },
  ])
  assert.equal(s.status, 'idle')
  s = voiceReducer(s, { type: 'REPLAY' })
  assert.equal(s.status, 'speaking')
  s = voiceReducer(s, { type: 'STOP_SPEAKING' })
  assert.equal(s.status, 'idle')
})

test('mic cannot start while transcribing or asking', () => {
  assert.equal(canStart('transcribing'), false)
  assert.equal(canStart('asking'), false)
  assert.equal(isBusy('asking'), true)
  const t = run([{ type: 'START' }, { type: 'STOP' }])
  assert.equal(voiceReducer(t, { type: 'START' }).status, 'transcribing')
  const a = run([{ type: 'SUBMIT', text: 'q' }])
  assert.equal(voiceReducer(a, { type: 'START' }).status, 'asking')
  assert.equal(voiceReducer(a, { type: 'SUBMIT', text: 'again' }).heard, 'q')
})

test('start while speaking interrupts the speech', () => {
  const sp = run([
    { type: 'SUBMIT', text: 'q' },
    { type: 'ANSWER', text: 'a', speak: true },
  ])
  assert.equal(voiceReducer(sp, { type: 'START' }).status, 'recording')
})

test('empty transcription is a noSpeech error; failures and dismiss', () => {
  let s = run([{ type: 'START' }, { type: 'STOP' }, { type: 'HEARD', text: '   ' }])
  assert.equal(s.status, 'error')
  assert.equal(s.error, 'noSpeech')
  s = voiceReducer(s, { type: 'DISMISS_ERROR' })
  assert.equal(s.status, 'idle')
  s = run([{ type: 'START' }, { type: 'FAIL', code: 'denied' }])
  assert.equal(s.error, 'denied')
  s = voiceReducer(s, { type: 'START' }) // can retry from error
  assert.equal(s.status, 'recording')
  assert.equal(s.error, null)
})

test('cancel returns to idle from recording/transcribing/asking, ignores late results', () => {
  const paths = [[{ type: 'START' }], [{ type: 'START' }, { type: 'STOP' }], [{ type: 'SUBMIT', text: 'q' }]]
  for (const evs of paths) {
    const s = voiceReducer(run(evs), { type: 'CANCEL' })
    assert.equal(s.status, 'idle')
    assert.equal(voiceReducer(s, { type: 'ANSWER', text: 'late', speak: true }).status, 'idle')
    assert.equal(voiceReducer(s, { type: 'HEARD', text: 'late' }).status, 'idle')
  }
})

test('SUBMIT ignores empty text', () => {
  assert.equal(voiceReducer(initialVoiceState, { type: 'SUBMIT', text: '  ' }).status, 'idle')
})

test('errorCodeForStatus', () => {
  assert.equal(errorCodeForStatus(400), 'badAudio')
  assert.equal(errorCodeForStatus(413), 'tooBig')
  assert.equal(errorCodeForStatus(422), 'noSpeech')
  assert.equal(errorCodeForStatus(429), 'serverBusy')
  assert.equal(errorCodeForStatus(502), 'serviceDown')
  assert.equal(errorCodeForStatus(503), 'serviceDown')
  assert.equal(errorCodeForStatus(401), 'signIn')
  assert.equal(errorCodeForStatus(null), 'network')
  assert.equal(errorCodeForStatus(500), 'unknown')
})
