import { useState } from 'react'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { fetchConsequences } from '../store/insightsSlice'
import type { RiskLevel } from '../types'

const sevTone: Record<RiskLevel, { pill: string; dot: string; label: string }> = {
  high: { pill: 'border-[#fb7185]/25 bg-[#fb7185]/10 text-[#fecdd3]', dot: 'bg-[#fb7185]', label: 'High' },
  medium: { pill: 'border-[#f5c26b]/25 bg-[#f5c26b]/10 text-[#fde68a]', dot: 'bg-[#f5c26b]', label: 'Medium' },
  low: { pill: 'border-[#34d399]/25 bg-[#34d399]/10 text-[#bbf7d0]', dot: 'bg-[#34d399]', label: 'Low' },
}

function LevelPill({ level, prefix }: { level: RiskLevel; prefix: string }) {
  const t = sevTone[level] || sevTone.medium
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${t.pill}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${t.dot}`} />
      {prefix} {t.label}
    </span>
  )
}

interface Props {
  documentId: string
}

export default function ConsequencesPanel({ documentId }: Props) {
  const dispatch = useAppDispatch()
  const { consequences, consequencesStatus, error } = useAppSelector((s) => s.insights)
  const [showHindi, setShowHindi] = useState(false)

  const run = (force = false) => dispatch(fetchConsequences({ documentId, force }))

  if (consequencesStatus === 'idle') {
    return (
      <div className="rounded-[26px] border border-[#fb7185]/16 bg-[#1c1418]/70 p-6 text-center sm:p-8">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-[20px] border border-[#fb7185]/25 bg-[#fb7185]/10 text-2xl">⚠️</div>
        <h3 className="mt-4 text-xl font-semibold text-white">What happens if I sign this?</h3>
        <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-400">
          Simulate the real-world consequences — money you could lose, rights you give up, and penalties you could face — if you sign this document as-is and things go wrong later.
        </p>
        <button type="button" onClick={() => run(false)} className="btn-primary mx-auto mt-5">
          Simulate consequences
        </button>
      </div>
    )
  }

  if (consequencesStatus === 'loading') {
    return (
      <div className="rounded-[26px] border border-white/8 bg-white/[0.02] p-8 text-center">
        <div className="mx-auto h-9 w-9 animate-spin rounded-full border-2 border-white/15 border-t-[#fb7185]" />
        <p className="mt-4 text-sm text-slate-400">Simulating what could happen if you sign…</p>
      </div>
    )
  }

  if (consequencesStatus === 'error') {
    return (
      <div className="rounded-[26px] border border-[#fb7185]/25 bg-[#2a1320]/65 p-6 text-sm text-[#fecdd3]">
        <p>{error || 'Could not generate the simulation.'}</p>
        <button type="button" onClick={() => run(true)} className="btn-secondary mt-4">Try again</button>
      </div>
    )
  }

  if (!consequences) return null

  return (
    <div className="space-y-4">
      <div className="info-card rounded-[24px] p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Your exposure if you sign</p>
            <LevelPill level={consequences.overall_exposure} prefix="Overall" />
          </div>
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
        <p className="mt-3 text-sm leading-7 text-slate-300">{consequences.overview}</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {consequences.scenarios.map((s) => {
          const tone = sevTone[s.severity] || sevTone.medium
          return (
            <div key={s.id} className={`section-card rounded-[24px] border-l-4 p-5 ${s.severity === 'high' ? 'border-l-[#fb7185]' : s.severity === 'medium' ? 'border-l-[#f5c26b]' : 'border-l-[#34d399]'}`}>
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[11px] uppercase tracking-[0.16em] text-slate-400">{s.category}</span>
                <LevelPill level={s.severity} prefix="Severity" />
                <LevelPill level={s.likelihood} prefix="Likelihood" />
              </div>
              <h4 className="mt-3 text-base font-semibold text-white">{s.title}</h4>
              <p className="mt-2 text-sm leading-6 text-slate-300">{showHindi ? s.plain_hindi : s.plain_english}</p>

              {s.outcome && (
                <div className="mt-3 rounded-[16px] border border-white/8 bg-white/[0.02] px-3.5 py-3">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">What happens</p>
                  <p className="mt-1 text-sm leading-6 text-slate-300">{s.outcome}</p>
                </div>
              )}
              {s.worst_case && (
                <div className={`mt-2 rounded-[16px] border px-3.5 py-3 ${tone.pill}`}>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.16em] opacity-80">Worst case</p>
                  <p className="mt-1 text-sm leading-6">{s.worst_case}</p>
                </div>
              )}
              <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                {s.trigger && <span>Triggered when: <span className="text-slate-400">{s.trigger}</span></span>}
                {s.related_clause && <span>Clause: <span className="text-slate-400">{s.related_clause}</span></span>}
              </div>
            </div>
          )
        })}
      </div>

      <p className="px-1 text-xs text-slate-500">
        AI simulation based on this document and Indian law — not a guarantee of outcomes. Consult a lawyer before signing.
      </p>
    </div>
  )
}
