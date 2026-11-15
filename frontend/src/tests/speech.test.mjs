/**
 * Text-to-speech pure helpers + controller (plain node --test, fake speechSynthesis).
 */
import test from 'node:test'
import assert from 'node:assert/strict'
import {
  toBcp47,
  stripForSpeech,
  chunkText,
  pickVoice,
  noticeFor,
  createSpeechController,
} from '../utils/speech.ts'

test('toBcp47 maps app languages and tolerates junk', () => {
  assert.equal(toBcp47('mr'), 'mr-IN')
  assert.equal(toBcp47('hi'), 'hi-IN')
  assert.equal(toBcp47('en'), 'en-IN')
  assert.equal(toBcp47('hi-IN'), 'hi-IN')
  assert.equal(toBcp47('MR_in'), 'mr-IN')
  assert.equal(toBcp47('fr'), 'en-IN')
  assert.equal(toBcp47(undefined), 'en-IN')
  assert.equal(toBcp47(null), 'en-IN')
})

test('stripForSpeech removes markdown, emoji and URLs', () => {
  const md = '# Title\n\n**Bold** and _italic_ text 😀 see [the guide](https://example.com/x) or https://foo.bar/baz now.\n- item one\n- item two\n`code`'
  const out = stripForSpeech(md)
  assert.ok(!/[*_#`]/.test(out), out)
  assert.ok(!/https?:|www\./.test(out), out)
  assert.ok(!/😀/u.test(out), out)
  assert.ok(out.includes('Bold and italic text'), out)
  assert.ok(out.includes('the guide'), out)
  assert.ok(out.includes('item one'), out)
  assert.ok(!out.includes('example.com'), out)
})

test('stripForSpeech turns line breaks into sentence breaks and keeps Devanagari', () => {
  const out = stripForSpeech('## शीर्षक\nपहली पंक्ति।\n\nदूसरी पंक्ति')
  assert.equal(out, 'शीर्षक. पहली पंक्ति। दूसरी पंक्ति.')
  assert.equal(stripForSpeech(''), '')
  assert.equal(stripForSpeech(null), '')
  assert.equal(stripForSpeech('⚖️ ✅ 🔒'), '')
})

test('stripForSpeech drops fenced code and tables', () => {
  const out = stripForSpeech('Before\n```js\nconst a = 1\n```\nAfter\n| a | b |\n|---|---|\n| 1 | 2 |')
  assert.ok(!out.includes('const'), out)
  assert.ok(out.includes('Before') && out.includes('After'))
  assert.ok(!out.includes('---'), out)
})

test('chunkText splits at sentence boundaries within the limit', () => {
  const text = 'First sentence is here. Second one follows! Is a third a question? Yes it is.'
  assert.deepEqual(chunkText(text, 200), [text])
  const small = chunkText(text, 40)
  assert.ok(small.length > 1)
  for (const c of small) assert.ok(c.length <= 40, `${c.length}: ${c}`)
  assert.equal(small.join(' '), text)
})

test('chunkText handles Devanagari danda and very long sentences', () => {
  const hi = 'यह पहला वाक्य है। यह दूसरा वाक्य है। यह तीसरा वाक्य है।'
  const parts = chunkText(hi, 30)
  assert.ok(parts.length >= 2)
  assert.ok(parts.every((p) => p.length <= 30))
  const long = Array.from({ length: 80 }, (_, i) => `word${i}`).join(' ') // no punctuation
  const lc = chunkText(long, 100)
  assert.ok(lc.length > 4)
  assert.ok(lc.every((c) => c.length <= 100))
  assert.equal(lc.join(' '), long)
  assert.deepEqual(chunkText('   '), [])
  assert.deepEqual(chunkText(''), [])
})

const V = (lang, name = lang, extra = {}) => ({ lang, name, ...extra })

test('pickVoice prefers an exact language match', () => {
  const voices = [V('en-US'), V('hi-IN'), V('mr-IN', 'Marathi Voice'), V('en-IN')]
  const c = pickVoice(voices, 'mr')
  assert.equal(c.voice.lang, 'mr-IN')
  assert.equal(c.match, 'exact')
  assert.equal(c.requested, 'mr-IN')
  assert.equal(pickVoice(voices, 'en').voice.lang, 'en-IN')
})

test('pickVoice falls back mr -> hi -> en with a match flag', () => {
  const c1 = pickVoice([V('en-US'), V('hi-IN')], 'mr')
  assert.equal(c1.voice.lang, 'hi-IN')
  assert.equal(c1.match, 'fallback-hi')
  assert.equal(noticeFor(c1, true), 'hindiVoice')

  const c2 = pickVoice([V('en-GB'), V('en-US')], 'mr')
  assert.equal(c2.match, 'fallback-en')
  assert.equal(noticeFor(c2, true), 'englishVoice')

  // Hindi has no Marathi-style fallback, only English
  const c3 = pickVoice([V('mr-IN'), V('en-US')], 'hi')
  assert.equal(c3.match, 'fallback-en')

  assert.equal(pickVoice([], 'hi'), null)
  assert.equal(noticeFor(null, true), 'noVoice')
  assert.equal(noticeFor(null, false), 'unsupported')
  assert.equal(noticeFor(pickVoice([V('hi-IN')], 'hi'), true), null)
})

test('pickVoice prefers regional match, quality hints and tolerates underscores', () => {
  const c = pickVoice([V('hi-US', 'plain'), V('hi_IN', 'plain'), V('hi-IN', 'Google Hindi')], 'hi')
  assert.equal(c.voice.name, 'Google Hindi')
  assert.equal(pickVoice([V('en_IN', 'x')], 'en').match, 'exact')
})

// --- controller with a fake engine ------------------------------------------------------------
function fakeEngine(voices) {
  const spoken = []
  const listeners = {}
  const synth = {
    speaking: false,
    paused: false,
    getVoices: () => voices,
    cancel() {
      synth.speaking = false
    },
    speak(u) {
      spoken.push(u)
      synth.speaking = true
      setTimeout(() => {
        synth.speaking = false
        u.onend?.()
      }, 1)
    },
    pause() {},
    resume() {},
    addEventListener(type, fn) {
      listeners[type] = fn
    },
    removeEventListener() {},
  }
  class Utterance {
    constructor(text) {
      this.text = text
      this.lang = ''
      this.voice = null
      this.rate = 1
      this.onend = null
      this.onerror = null
    }
  }
  return { synth, Utterance, spoken, listeners }
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms))

test('controller speaks chunks in order, reports state, uses chosen voice', async () => {
  const hi = V('hi-IN', 'Hindi Voice')
  const { synth, Utterance, spoken } = fakeEngine([hi])
  const c = createSpeechController(synth, Utterance, 'mr')
  assert.equal(c.getState().isSupported, true)
  assert.equal(c.getState().notice, 'hindiVoice')
  let ended = false
  c.speak('One sentence here. Another sentence there. **Third** one.', { key: 'k1', onEnd: () => (ended = true) })
  assert.equal(c.getState().isSpeaking, true)
  assert.equal(c.getState().activeKey, 'k1')
  await wait(60)
  assert.ok(spoken.length >= 1)
  assert.equal(spoken[0].voice, hi)
  assert.equal(spoken[0].lang, 'hi-IN')
  assert.ok(!spoken.map((u) => u.text).join(' ').includes('*'))
  assert.equal(ended, true)
  assert.equal(c.getState().isSpeaking, false)
  c.destroy()
})

test('controller stop() cancels and a new speak() replaces the old one', async () => {
  const { synth, Utterance, spoken } = fakeEngine([V('en-IN')])
  const c = createSpeechController(synth, Utterance, 'en')
  c.speak('Alpha. Beta. Gamma.', { key: 'a' })
  c.stop()
  assert.equal(c.getState().isSpeaking, false)
  await wait(20)
  assert.equal(spoken.length, 0) // stopped before the deferred first chunk
  c.speak('Hello there.', { key: 'b' })
  await wait(40)
  assert.equal(spoken.length, 1)
  c.destroy()
})

test('controller waits for voiceschanged and never throws when unsupported', async () => {
  const voices = []
  const { synth, Utterance, listeners } = fakeEngine(voices)
  const c = createSpeechController(synth, Utterance, 'hi')
  assert.equal(c.getState().voicesReady, false)
  assert.equal(c.getState().choice, null)
  voices.push(V('hi-IN', 'Late voice'))
  listeners.voiceschanged()
  assert.equal(c.getState().voicesReady, true)
  assert.equal(c.getState().choice.voice.name, 'Late voice')
  c.destroy()

  const none = createSpeechController(null, null, 'en')
  assert.equal(none.getState().isSupported, false)
  assert.equal(none.getState().notice, 'unsupported')
  none.speak('hello')
  none.stop()
  none.setLanguage('hi')
  none.destroy()

  const throwing = createSpeechController(
    { ...fakeEngine([]).synth, getVoices() { throw new Error('boom') } },
    fakeEngine([]).Utterance,
    'en',
  )
  assert.equal(throwing.getState().choice, null)
})
