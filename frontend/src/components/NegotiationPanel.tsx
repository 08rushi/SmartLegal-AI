import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { fetchNegotiation } from '../store/insightsSlice'
import { getCurrentLang } from '../services/api'
import RiskBadge from './RiskBadge'
import { localizeKnownError } from '../utils/i18nHelpers'

interface Props {
  documentId: string
}

function CopyButton({ text }: { text: string }) {
  const { t } = useTranslation('insights')
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    } catch {
      /* clipboard blocked — ignore */
    }
  }
  return (
    <button
      type="button"
      onClick={copy}
      className={`rounded-full border px-3 py-1 text-xs transition ${copied ? 'border-[#34d399]/30 bg-[#34d399]/10 text-[#bbf7d0]' : 'border-white/10 bg-white/[0.03] text-slate-400 hover:text-white'}`}
    >
      {copied ? t('negotiation.copied') : t('negotiation.copy')}
    </button>
  )
}

export default function NegotiationPanel({ documentId }: Props) {
  const dispatch = useAppDispatch()
  const { negotiation, negotiationStatus, negotiationLang, error } = useAppSelector((s) => s.insights)
  const { t } = useTranslation('insights')
  // The backend answers in the language sent in X-Lang and caches per language, so the content is
  // already in the app language (en / hi / mr); no per-panel language toggle is needed.
  const lang = getCurrentLang()

  const run = (force = false) => dispatch(fetchNegotiation({ documentId, force, lang }))

  // Language changed after the result was generated -> fetch it again in the new language.
  useEffect(() => {
    if (negotiationStatus !== 'idle' && negotiationLang && negotiationLang !== lang) {
      dispatch(fetchNegotiation({ documentId, force: false, lang }))
    }
  }, [dispatch, documentId, lang, negotiationLang, negotiationStatus])

  if (negotiationStatus === 'idle') {
    return (
      <div className="rounded-[26px] border border-[#8a5cff]/16 bg-[#161428]/70 p-6 text-center sm:p-8">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-[20px] border border-[#8a5cff]/25 bg-[#8a5cff]/10 text-2xl">🤝</div>
        <h3 className="mt-4 text-xl font-semibold text-white">{t('negotiation.idleTitle')}</h3>
        <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-400">{t('negotiation.idleBody')}</p>
        <button type="button" onClick={() => run(false)} className="btn-primary mx-auto mt-5">
          {t('negotiation.idleCta')}
        </button>
      </div>
    )
  }

  if (negotiationStatus === 'loading') {
    return (
      <div className="rounded-[26px] border border-white/8 bg-white/[0.02] p-8 text-center">
        <div className="mx-auto h-9 w-9 animate-spin rounded-full border-2 border-white/15 border-t-[#8a5cff]" />
        <p className="mt-4 text-sm text-slate-400">{t('negotiation.loading')}</p>
      </div>
    )
  }

  if (negotiationStatus === 'error') {
    return (
      <div className="rounded-[26px] border border-[#fb7185]/25 bg-[#2a1320]/65 p-6 text-sm text-[#fecdd3]">
        <p>{localizeKnownError(t, error) || t('negotiation.errorFallback')}</p>
        <button type="button" onClick={() => run(true)} className="btn-secondary mt-4">{t('common.tryAgain')}</button>
      </div>
    )
  }

  if (!negotiation) return null

  return (
    <div className="space-y-4">
      <div className="info-card rounded-[24px] p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">{t('negotiation.strategy')}</p>
          <div className="flex items-center gap-2">
            <button type="button" onClick={() => run(true)} className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-slate-400 transition hover:text-white">
              {t('common.regenerate')}
            </button>
          </div>
        </div>
        <p className="mt-3 text-sm leading-7 text-slate-300">{negotiation.summary}</p>
      </div>

      <div className="space-y-4">
        {negotiation.items.map((it) => (
          <div key={it.id} className="section-card rounded-[24px] p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <h4 className="text-base font-semibold text-white">{it.clause_title}</h4>
              <RiskBadge level={it.risk_level} />
            </div>

            {it.current_problem && (
              <p className="mt-2 text-sm leading-6 text-[#fecdd3]/90">
                <span className="font-medium text-[#fb7185]">{t('negotiation.problem')} </span>{it.current_problem}
              </p>
            )}

            <div className="mt-3 rounded-[16px] border border-white/8 bg-white/[0.02] px-3.5 py-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">{t('negotiation.askInstead')}</p>
              <p className="mt-1 text-sm leading-6 text-slate-300">{it.suggested_change || it.plain_hindi}</p>
            </div>

            {it.counter_text && (
              <div className="mt-2 rounded-[16px] border border-[#8a5cff]/18 bg-[#0c0f1f]/70 px-3.5 py-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#c5b4ff]">{t('negotiation.counterClause')}</p>
                  <CopyButton text={it.counter_text} />
                </div>
                <p className="mt-2 whitespace-pre-wrap font-mono text-xs leading-6 text-slate-300">{it.counter_text}</p>
              </div>
            )}

            {it.talking_point && (
              <p className="mt-3 text-sm leading-6 text-slate-400">
                <span className="font-medium text-[#f5c26b]">{t('negotiation.sayThis')} </span>{it.talking_point}
              </p>
            )}
          </div>
        ))}
      </div>

      <p className="px-1 text-xs text-slate-500">
        {t('negotiation.disclaimer')}
      </p>
    </div>
  )
}
