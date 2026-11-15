import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { UseVoiceAsk } from '../../hooks/useVoiceAsk'
import { LANGUAGES, normalizeLanguage } from '../../i18n/languages'
import type { VoiceErrorCode } from '../../utils/voiceMachine'
import MarkdownMessage from '../MarkdownMessage'
import { SpeechNotice } from '../ui/SpeechNotice'
import { voiceStatusText } from './VoiceButton'

const SERVER_TEXT_CODES: VoiceErrorCode[] = ['tooBig', 'badAudio', 'noSpeech', 'serverBusy', 'serviceDown']

/**
 * Compact voice status panel: what is happening, what was heard (editable), the answer with listen/stop,
 * errors and the auto-read toggle. The mic itself (`VoiceButton`) sits beside the page's text input.
 * The page supplies `voice = useVoiceAsk({ ask })`.
 */
export function VoiceConversationPanel({ voice, className = '' }: { voice: UseVoiceAsk; className?: string }) {
  const { t, i18n } = useTranslation('voice')
  const { state, source } = voice
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')

  const langCode = normalizeLanguage(state.heardLang) ?? normalizeLanguage(i18n.resolvedLanguage || i18n.language) ?? 'en'
  const langName = LANGUAGES.find((l) => l.code === langCode)?.nativeName ?? langCode
  const busy = state.status === 'transcribing' || state.status === 'asking'
  const showCancel = state.status === 'recording' || busy

  const errorText = (() => {
    if (!state.error) return ''
    if (state.errorDetail && SERVER_TEXT_CODES.includes(state.error)) return state.errorDetail // already localized by the server
    return t(`errors.${state.error}.text`)
  })()

  const startEdit = () => {
    setDraft(state.heard)
    setEditing(true)
  }
  const send = () => {
    const text = draft.trim()
    if (!text) return
    setEditing(false)
    voice.submitText(text)
  }

  const level = state.status === 'recording' && source === 'server' ? voice.recorder.level : 0
  const idleQuiet = state.status === 'idle' && !state.heard && !state.answer && !state.error && source !== 'none'

  return (
    <section aria-label={t('panelLabel')} className={`panel-muted rounded-[20px] p-3 sm:p-4 ${className}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p role="status" aria-live="polite" className="text-xs text-slate-300 sm:text-sm">
          {idleQuiet ? (source === 'browser' ? t('hintBrowser') : t('hint')) : voiceStatusText(voice, t)}
        </p>
        <div className="flex items-center gap-3">
          {showCancel && (
            <button type="button" onClick={voice.cancel} className="btn-secondary px-3 py-1 text-xs">
              {t('cancel')}
            </button>
          )}
          {voice.speechSupported && (
            <label className="flex cursor-pointer items-center gap-2 text-xs text-slate-400">
              <input
                type="checkbox"
                checked={voice.autoSpeak}
                onChange={(e) => voice.setAutoSpeak(e.target.checked)}
                className="h-4 w-4 shrink-0 accent-[#f5c26b]"
              />
              <span>{t('autoSpeak')}</span>
            </label>
          )}
        </div>
      </div>

      {state.status === 'recording' && source === 'server' && (
        <div
          role="meter"
          aria-label={t('meter')}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(level * 100)}
          className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-white/10"
        >
          <div className="h-full bg-[#f5c26b]" style={{ width: `${Math.round(level * 100)}%`, transition: 'width 80ms linear' }} />
        </div>
      )}

      {source === 'none' && state.status !== 'error' && <p className="mt-2 text-xs text-slate-400">{t('notSupported')}</p>}

      {state.status === 'error' && state.error && (
        <div role="alert" className="mt-3 rounded-2xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs leading-5 text-rose-200 sm:text-sm">
          <div className="flex items-start justify-between gap-2">
            <p className="font-semibold">{t(`errors.${state.error}.title`)}</p>
            <button type="button" onClick={voice.dismissError} aria-label={t('cancel')} className="text-rose-200 hover:text-white">
              ✕
            </button>
          </div>
          <p className="mt-1">{errorText}</p>
          {state.error === 'denied' && <p className="mt-1">{t('errors.denied.how')}</p>}
          {(state.error === 'insecure' || state.error === 'unsupported') && <p className="mt-1">{t('secureNote')}</p>}
          <p className="mt-1">{t('typeInstead')}</p>
        </div>
      )}

      {state.heard && (
        <div className="mt-3 rounded-2xl border border-white/10 bg-white/[0.03] p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-xs font-semibold text-white sm:text-sm">{t('heard.title')}</h3>
            <span className="rounded-full border border-[#f5c26b]/25 bg-[#f5c26b]/10 px-3 py-0.5 text-xs text-[#f5c26b]">
              {t('langChip', { name: langName })}
            </span>
          </div>
          {editing ? (
            <div className="mt-2 space-y-2">
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                rows={3}
                aria-label={t('heard.editLabel')}
                className="input-field w-full resize-y text-sm"
              />
              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={send} disabled={!draft.trim() || busy} className="btn-primary px-4 py-1.5 text-xs disabled:opacity-60">
                  {t('heard.send')}
                </button>
                <button type="button" onClick={() => setEditing(false)} className="btn-secondary px-4 py-1.5 text-xs">
                  {t('heard.cancelEdit')}
                </button>
              </div>
            </div>
          ) : (
            <>
              <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-100">{state.heard}</p>
              {!busy && state.status !== 'recording' && (
                <button type="button" onClick={startEdit} className="mt-2 text-xs text-[#f5c26b] hover:underline">
                  {t('heard.edit')}
                </button>
              )}
            </>
          )}
        </div>
      )}

      {state.answer && (
        <div className="mt-3 rounded-2xl border border-[#f5c26b]/30 bg-white/[0.03] p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-xs font-semibold text-white sm:text-sm">{t('answer.title')}</h3>
            {voice.speechSupported &&
              (state.status === 'speaking' ? (
                <button type="button" onClick={voice.stopSpeaking} className="btn-secondary px-3 py-1 text-xs">
                  <span aria-hidden="true">⏹</span> {t('answer.stop')}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={voice.replay}
                  disabled={state.status !== 'idle'}
                  className="btn-secondary px-3 py-1 text-xs disabled:opacity-50"
                >
                  <span aria-hidden="true">🔊</span> {t('answer.replay')}
                </button>
              ))}
          </div>
          <div className="mt-2 max-h-40 overflow-y-auto text-sm text-slate-200">
            <MarkdownMessage content={state.answer} />
          </div>
          <SpeechNotice className="mt-2" />
        </div>
      )}
    </section>
  )
}

export default VoiceConversationPanel
