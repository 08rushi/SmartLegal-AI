import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { fetchNegotiation } from '../store/insightsSlice'
import RiskBadge from './RiskBadge'

interface Props {
  documentId: string
}

function CopyButton({ text }: { text: string }) {
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
      {copied ? 'Copied ✓' : 'Copy'}
    </button>
  )
}

export default function NegotiationPanel({ documentId }: Props) {
  const dispatch = useAppDispatch()
  const { negotiation, negotiationStatus, error } = useAppSelector((s) => s.insights)
  const [showHindi, setShowHindi] = useState(false)

  const run = (force = false) => dispatch(fetchNegotiation({ documentId, force }))

  if (negotiationStatus === 'idle') {
    return (
      <div className="rounded-[26px] border border-[#8a5cff]/16 bg-[#161428]/70 p-6 text-center sm:p-8">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-[20px] border border-[#8a5cff]/25 bg-[#8a5cff]/10 text-2xl">🤝</div>
        <h3 className="mt-4 text-xl font-semibold text-white">Negotiate better terms</h3>
        <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-400">
          Get fairer alternatives for the risky clauses — with copy-ready replacement wording you can send to the other party and a talking point for each.
        </p>
        <button type="button" onClick={() => run(false)} className="btn-primary mx-auto mt-5">
          Get negotiation tips
        </button>
      </div>
    )
  }

  if (negotiationStatus === 'loading') {
    return (
      <div className="rounded-[26px] border border-white/8 bg-white/[0.02] p-8 text-center">
        <div className="mx-auto h-9 w-9 animate-spin rounded-full border-2 border-white/15 border-t-[#8a5cff]" />
        <p className="mt-4 text-sm text-slate-400">Preparing safer clauses and counter-proposals…</p>
      </div>
    )
  }

  if (negotiationStatus === 'error') {
    return (
      <div className="rounded-[26px] border border-[#fb7185]/25 bg-[#2a1320]/65 p-6 text-sm text-[#fecdd3]">
        <p>{error || 'Could not generate negotiation guidance.'}</p>
        <button type="button" onClick={() => run(true)} className="btn-secondary mt-4">Try again</button>
      </div>
    )
  }

  if (!negotiation) return null

  return (
    <div className="space-y-4">
      <div className="info-card rounded-[24px] p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Your negotiation strategy</p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowHindi((v) => !v)}
              className={`rounded-full border px-3 py-1 text-xs transition ${showHindi ? 'border-[#f5c26b]/25 bg-[#f5c26b]/10 text-[#f5c26b]' : 'border-white/10 bg-white/[0.03] text-slate-400 hover:text-white'}`}
            >
              {showHindi ? 'Hindi' : 'English'}
            </button>
            <button type="button" onClick={() => run(true)} className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-slate-400 transition hover:text-white">
              Regenerate
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
                <span className="font-medium text-[#fb7185]">Problem: </span>{it.current_problem}
              </p>
            )}

            <div className="mt-3 rounded-[16px] border border-white/8 bg-white/[0.02] px-3.5 py-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Ask for instead</p>
              <p className="mt-1 text-sm leading-6 text-slate-300">{showHindi ? it.plain_hindi : it.suggested_change}</p>
            </div>

            {it.counter_text && (
              <div className="mt-2 rounded-[16px] border border-[#8a5cff]/18 bg-[#0c0f1f]/70 px-3.5 py-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[#c5b4ff]">Copy-ready counter clause</p>
                  <CopyButton text={it.counter_text} />
                </div>
                <p className="mt-2 whitespace-pre-wrap font-mono text-xs leading-6 text-slate-300">{it.counter_text}</p>
              </div>
            )}

            {it.talking_point && (
              <p className="mt-3 text-sm leading-6 text-slate-400">
                <span className="font-medium text-[#f5c26b]">Say this: </span>{it.talking_point}
              </p>
            )}
          </div>
        ))}
      </div>

      <p className="px-1 text-xs text-slate-500">
        AI-suggested wording based on Indian law — review with a lawyer before sending. Not legal advice.
      </p>
    </div>
  )
}
