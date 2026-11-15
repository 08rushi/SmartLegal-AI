import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import RiskBadge from '../RiskBadge'
import { Card } from '../Card'
import { SpeakButton } from '../ui/SpeakButton'
import { SpeechNotice } from '../ui/SpeechNotice'
import type { RiskLevel } from '../../types'
import type { MoneyDates, VerdictLevel, VerdictView } from '../../utils/analysisVerdict'

const SMALL_SPEAKER = '!h-9 !w-9 !rounded-xl'

// Same palette as the clause cards: rose / amber / emerald panels with an emoji marker.
const TONE: Record<VerdictLevel, { box: string; chip: string; text: string; emoji: string }> = {
  safe: {
    box: 'border-[#34d399]/25 bg-[#10241f]/55',
    chip: 'border-[#34d399]/25 bg-[#34d399]/10',
    text: 'text-[#bbf7d0]',
    emoji: '✅',
  },
  careful: {
    box: 'border-[#f5c26b]/25 bg-[#2a2410]/55',
    chip: 'border-[#f5c26b]/25 bg-[#f5c26b]/10',
    text: 'text-[#fde68a]',
    emoji: '⚠️',
  },
  avoid: {
    box: 'border-[#fb7185]/25 bg-[#2a1320]/55',
    chip: 'border-[#fb7185]/25 bg-[#fb7185]/10',
    text: 'text-[#fecdd3]',
    emoji: '⛔',
  },
}

const RISK_LINE: Record<string, string> = {
  high: 'border-l-[#fb7185]',
  medium: 'border-l-[#f5c26b]',
  low: 'border-l-[#34d399]',
}

/** (1) The verdict: emoji + short word + one plain sentence + speaker. */
export function VerdictCard({ view }: { view: VerdictView }) {
  const { t } = useTranslation('verdict')
  const [spoke, setSpoke] = useState(false)
  const tone = TONE[view.verdict.level]
  return (
    <Card as="section" variant="section" aria-labelledby="verdict-heading" className={`rounded-[30px] border p-5 sm:p-6 ${tone.box}`}>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex min-w-0 items-center gap-4">
          <div
            className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-[20px] border text-2xl ${tone.chip}`}
            aria-hidden="true"
          >
            {tone.emoji}
          </div>
          <h2 id="verdict-heading" className={`text-2xl font-semibold ${tone.text}`}>
            {view.levelText}
          </h2>
        </div>
        <SpeakButton text={view.speech} label={t('listen')} onSpeak={() => setSpoke(true)} className={SMALL_SPEAKER} />
      </div>
      <p className="mt-4 text-sm leading-7 text-slate-200">{view.sentence}</p>
      {view.docType && <p className="mt-2 text-xs text-slate-400">{t('docType', { type: view.docType })}</p>}
      <SpeechNotice show={spoke} className="mt-4" />
    </Card>
  )
}

/** (2) Up to three key risks, each with a speaker and a jump link to the full clause. */
export function KeyRisks({ view, onJump }: { view: VerdictView; onJump: (index: number) => void }) {
  const { t } = useTranslation('verdict')
  return (
    <Card as="section" variant="section" aria-labelledby="risks-heading" className="scroll-mt-28 rounded-[30px] p-5 sm:p-6">
      <h2 id="risks-heading" className="text-2xl font-semibold text-white">
        {t('risks.title')}
      </h2>
      {view.risks.length === 0 ? (
        <p className="mt-3 text-sm leading-7 text-slate-300">{t('risks.none')}</p>
      ) : (
        <ol className="mt-5 space-y-4">
          {view.risks.map((r, i) => (
            <li key={`${r.index}-${i}`}>
              <div className={`info-card rounded-[22px] border-l-4 p-4 ${RISK_LINE[r.riskLevel] ?? RISK_LINE.medium}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <RiskBadge level={r.riskLevel as RiskLevel} />
                    <h3 className="mt-3 text-lg font-semibold text-white">{r.title}</h3>
                  </div>
                  <SpeakButton text={[r.title, r.text].filter(Boolean).join('\n')} label={r.title} className={SMALL_SPEAKER} />
                </div>
                {r.text && <p className="mt-2 text-sm leading-7 text-slate-300">{r.text}</p>}
                <button type="button" onClick={() => onJump(r.index)} className="btn-secondary mt-3 px-4 py-2.5 text-sm">
                  {t('risks.seeClause')}
                </button>
              </div>
            </li>
          ))}
        </ol>
      )}
    </Card>
  )
}

/** (3) Up to three numbered next steps (+ lawyer button when the risk is high). */
export function NextSteps({ view, onLawyer }: { view: VerdictView; onLawyer: () => void }) {
  const { t } = useTranslation('verdict')
  if (view.steps.length === 0 && !view.verdict.suggestLawyer) return null
  return (
    <Card as="section" variant="section" aria-labelledby="steps-heading" className="scroll-mt-28 rounded-[30px] p-5 sm:p-6">
      <h2 id="steps-heading" className="text-2xl font-semibold text-white">
        {t('steps.title')}
      </h2>
      {view.steps.length > 0 && (
        <ol className="mt-5 space-y-3">
          {view.steps.map((text, i) => (
            <li key={i} className="metric-card flex items-start gap-4 rounded-[22px] p-4">
              <span aria-hidden="true" className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-[#f5c26b]/20 bg-[#f5c26b]/10 text-sm font-semibold text-[#f5c26b]">
                {i + 1}
              </span>
              <p className="min-w-0 pt-1.5 text-sm leading-7 text-slate-200">{text}</p>
            </li>
          ))}
        </ol>
      )}
      {view.verdict.suggestLawyer && (
        <div className="mt-5 flex flex-wrap items-center gap-4">
          <button type="button" onClick={onLawyer} className="btn-primary">
            <span aria-hidden="true">⚖️</span> {t('steps.lawyer')}
          </button>
          <p className="max-w-md text-sm text-slate-400">{t('steps.lawyerHint')}</p>
        </div>
      )}
    </Card>
  )
}

/** (4) Amounts, deadlines and notice periods that were already extracted. Renders nothing when there are none. */
export function MoneyDatesStrip({ data }: { data: MoneyDates }) {
  const { t } = useTranslation('verdict')
  if (data.amounts.length === 0 && data.dates.length === 0) return null
  return (
    <Card as="section" variant="section" aria-labelledby="money-heading" className="rounded-[30px] p-5 sm:p-6">
      <h2 id="money-heading" className="text-2xl font-semibold text-white">
        {t('money.title')}
      </h2>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        {data.amounts.length > 0 && (
          <div className="info-card rounded-[22px] p-4">
            <p className="text-sm font-medium text-[#f5c26b]">
              <span aria-hidden="true">💰</span> {t('money.amounts')}
            </p>
            <ul className="mt-3 space-y-2 text-sm leading-7 text-slate-300">
              {data.amounts.map((a) => (
                <li key={a}>• {a}</li>
              ))}
            </ul>
          </div>
        )}
        {data.dates.length > 0 && (
          <div className="info-card rounded-[22px] p-4">
            <p className="text-sm font-medium text-[#f5c26b]">
              <span aria-hidden="true">📅</span> {t('money.dates')}
            </p>
            <ul className="mt-3 space-y-2 text-sm leading-7 text-slate-300">
              {data.dates.map((d, i) => (
                <li key={`${d.label}-${d.date}-${i}`}>
                  {d.notice && (
                    <span className="mr-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-0.5 text-[11px] font-medium text-amber-300">
                      {t('money.notice')}
                    </span>
                  )}
                  <span className="text-slate-500">{d.label}:</span> {d.date}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Card>
  )
}
