import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { Clause } from '../types'
import RiskBadge from './RiskBadge'
import { Card } from './Card'
import { SpeakButton } from './ui/SpeakButton'
import { UnclearTextPill } from './analysis/UnclearTextPill'
import { enumLabel, enumSlug } from '../utils/i18nHelpers'

interface Props {
  clause: Clause
  index: number
  /** Open the card (used by the "see full clause" jump from the key risks). */
  forceOpen?: boolean
}

const toneMap = {
  high: {
    line: 'border-l-[#fb7185]',
    panel: 'bg-[#2a1320]/65 border-[#fb7185]/20',
    text: 'text-[#fecdd3]',
  },
  medium: {
    line: 'border-l-[#f5c26b]',
    panel: 'bg-[#2a2410]/60 border-[#f5c26b]/20',
    text: 'text-[#fde68a]',
  },
  low: {
    line: 'border-l-[#34d399]',
    panel: 'bg-[#10241f]/60 border-[#34d399]/20',
    text: 'text-[#bbf7d0]',
  },
}

function renderTextWithUnclear(text: string) {
  if (!text || !text.includes('[UNCLEAR]')) {
    return text
  }
  const parts = text.split(/(\[UNCLEAR\])/g)
  return parts.map((part, index) => {
    if (part === '[UNCLEAR]') {
      return <UnclearTextPill key={index} />
    }
    return part
  })
}

export default function ClauseCard({ clause, index, forceOpen = false }: Props) {
  const [expanded, setExpanded] = useState(clause.risk_level === 'high' || forceOpen)
  useEffect(() => {
    if (forceOpen) setExpanded(true)
  }, [forceOpen])
  // `clause` is already the view for the app language: for hi / mr the Analysis page passes the
  // AI-translated clause (`original_text` stays the document's own wording). So `plain_english` is the
  // explanation in the *app* language. The toggle keeps only what is not redundant: in English the extra
  // Hindi text, and for any language the explanation in the document's own language.
  const { t, i18n } = useTranslation(['clauses', 'verdict'])
  const globalLang = (i18n.language || 'en').slice(0, 2)
  const [lang, setLang] = useState<'en' | 'hi' | 'src'>('en')
  // Back to the app-language text when the user switches the app language.
  useEffect(() => {
    setLang('en')
  }, [globalLang])
  const clauseNum = (clause as Clause & { clause_number?: string }).clause_number
  const pageNum = (clause as Clause & { page_number?: string | number }).page_number
  const tone = toneMap[clause.risk_level] ?? toneMap.medium

  const hasUnclear =
    Boolean(clause.is_unclear) ||
    Boolean(clause.original_text && clause.original_text.includes('[UNCLEAR]')) ||
    Boolean(clause.plain_english && clause.plain_english.includes('[UNCLEAR]'))

  // Show the "original language" option only for non-English documents that have it.
  const sourceLang = (clause.source_language || '').trim()
  const hasSource =
    Boolean(clause.plain_source && clause.plain_source.trim()) &&
    sourceLang.toLowerCase() !== 'english' &&
    // not offered separately when the document's language is already the app language
    !(globalLang === 'hi' && sourceLang.toLowerCase() === 'hindi') &&
    !(globalLang === 'mr' && sourceLang.toLowerCase() === 'marathi')
  // Very long documents are analysed in compact mode (no Hindi text) to fit free-tier AI limits.
  const hasHindi = Boolean(clause.plain_hindi && clause.plain_hindi.trim())
  const appLangLabel = t(`clauses:languages.${globalLang === 'hi' ? 'hindi' : globalLang === 'mr' ? 'marathi' : 'english'}`)
  const langOptions: [typeof lang, string][] = [
    ['en', appLangLabel],
    ...(globalLang === 'en' && hasHindi ? ([['hi', t('clauses:languages.hindi')]] as [typeof lang, string][]) : []),
    ...(hasSource
      ? ([['src', sourceLang ? t(`clauses:languages.${enumSlug(sourceLang)}`, { defaultValue: sourceLang }) : t('clauses:card.original')]] as [typeof lang, string][])
      : []),
  ]
  const plainText =
    lang === 'hi'
      ? clause.plain_hindi
      : lang === 'src'
      ? clause.plain_source || clause.plain_english
      : clause.plain_english

  const showReason = Boolean(clause.risk_reason) && clause.risk_level !== 'low'
  // Lines become sentence breaks in the speech cleaner, so no translated sentence is glued together.
  const speakText = [clause.title, clause.plain_english, showReason ? clause.risk_reason : '']
    .filter(Boolean)
    .join('\n')

  return (
    <Card variant="section" id={`clause-${clause.id}`} className={`scroll-mt-28 overflow-hidden rounded-[26px] border-l-4 ${tone.line}`}>
      <div className="flex items-start">
        <button
          type="button"
          onClick={() => setExpanded((value) => !value)}
          aria-expanded={expanded}
          aria-label={t('clauses:card.ariaLabel', {
            num: index + 1,
            title: clause.title,
            risk: t(`clauses:risk.${clause.risk_level}`, { defaultValue: String(clause.risk_level) }),
            action: expanded ? t('clauses:card.collapse') : t('clauses:card.expand'),
          })}
          className="flex min-w-0 flex-1 items-start justify-between gap-4 px-5 py-5 text-left transition hover:bg-white/[0.02] sm:px-6 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-inset"
        >
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[11px] uppercase tracking-[0.2em] text-slate-500">
                {String(index + 1).padStart(2, '0')}
              </span>
              <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[11px] text-slate-400">
                {enumLabel(t, 'clauses:types', clause.clause_type)}
              </span>
              {clauseNum && clauseNum !== 'Unnumbered clause' && (
                <span className="rounded-full border border-[#8a5cff]/25 bg-[#8a5cff]/10 px-2.5 py-1 text-[11px] text-[#c5b4ff]">
                  {clauseNum}
                </span>
              )}
              {pageNum && (
                <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[11px] text-slate-400">
                  {t('clauses:card.page', { page: pageNum })}
                </span>
              )}
              {hasUnclear && (
                <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-[11px] text-amber-300 font-medium">
                  ⚠️ {t('clauses:card.containsUnclear')}
                </span>
              )}
            </div>

            <h3 className="mt-4 text-lg font-semibold text-white sm:text-xl">{clause.title}</h3>
            <p className="mt-2 line-clamp-2 text-sm leading-7 text-slate-400">
              {renderTextWithUnclear(clause.plain_english)}
            </p>
          </div>

          <div className="flex shrink-0 items-center gap-3">
            <RiskBadge level={clause.risk_level} score={clause.risk_score} />
            <span className="mt-0.5 text-sm text-slate-500" aria-hidden="true">{expanded ? '▲' : '▼'}</span>
          </div>
        </button>
        <SpeakButton text={speakText} label={t('verdict:clause.listen')} className="mr-4 mt-4 !h-9 !w-9 !rounded-xl sm:mr-5" />
      </div>

      {expanded && (
        <div className="border-t border-white/8 px-5 pb-5 pt-5 sm:px-6 sm:pb-6 space-y-4">
          {hasUnclear && (
            <div className="rounded-[22px] border border-amber-500/30 bg-amber-500/10 p-4 space-y-1.5 text-xs text-amber-200">
              <div className="font-semibold text-amber-300 flex items-center gap-1.5">
                <span aria-hidden="true">⚠️</span>
                <span>{t('clauses:card.scanTitle')}</span>
              </div>
              <p className="leading-relaxed">{t('clauses:card.scanBody')}</p>
            </div>
          )}

          <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
            <div className="space-y-4">
              {showReason && (
                <div className={`rounded-[22px] border px-4 py-4 ${tone.panel}`}>
                  <p className={`text-xs font-semibold uppercase tracking-[0.2em] ${tone.text}`}>
                    {t(`clauses:tone.${clause.risk_level}`, { defaultValue: '' })}
                  </p>
                  <p className="mt-2 text-sm leading-7 text-slate-200">{clause.risk_reason}</p>
                </div>
              )}

              <Card variant="info" className="rounded-[22px] px-4 py-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{t('clauses:card.plainLanguage')}</p>
                  {langOptions.length > 1 && (
                    <div className="flex items-center gap-0.5 rounded-full border border-white/10 bg-white/[0.03] p-0.5">
                      {langOptions.map(([key, label]) => (
                        <button
                          key={key}
                          type="button"
                          onClick={() => setLang(key)}
                          aria-pressed={lang === key}
                          className={`rounded-full px-3 py-1 text-xs transition ${
                            lang === key ? 'bg-[#f5c26b]/15 text-[#f5c26b]' : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <div className="text-sm leading-7 text-slate-300">{renderTextWithUnclear(plainText)}</div>
              </Card>
            </div>

            <details className="info-card h-fit rounded-[22px] px-4 py-4">
              <summary className="cursor-pointer text-sm font-medium text-white">{t('clauses:card.viewOriginal')}</summary>
              <div className="mt-4 whitespace-pre-wrap font-mono text-xs leading-7 text-slate-400">
                {renderTextWithUnclear(clause.original_text)}
              </div>
            </details>
          </div>
        </div>
      )}
    </Card>
  )
}
