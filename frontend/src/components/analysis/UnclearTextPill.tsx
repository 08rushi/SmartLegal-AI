import { useState } from 'react'

interface UnclearTextPillProps {
  label?: string
  guidanceText?: string
}

export function UnclearTextPill({
  label = '[Unclear in Source]',
  guidanceText = 'Portions of this text could not be reliably read from the physical scan or photo (e.g. ink stamp, fold, or low resolution). Verify against the original physical paper before acting.',
}: UnclearTextPillProps) {
  const [showTooltip, setShowTooltip] = useState(false)

  return (
    <span className="relative inline-block align-baseline my-0.5">
      <button
        type="button"
        onClick={() => setShowTooltip((prev) => !prev)}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onFocus={() => setShowTooltip(true)}
        onBlur={() => setShowTooltip(false)}
        aria-label="Text unclear in source document scan. Click or focus for physical verification guidance."
        aria-expanded={showTooltip}
        className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-amber-500/15 border border-amber-400/40 text-amber-300 font-mono text-xs font-semibold hover:bg-amber-500/25 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-1 focus:ring-offset-[#0b1120] transition cursor-pointer"
      >
        <span aria-hidden="true" className="text-amber-400 text-xs">⚠️</span>
        <span>{label}</span>
      </button>

      {showTooltip && (
        <span
          role="tooltip"
          className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 max-w-[85vw] p-3 rounded-xl bg-slate-900/95 border border-amber-400/40 text-xs text-amber-100/90 shadow-2xl backdrop-blur-md pointer-events-none animate-fadeIn block text-left font-sans normal-case tracking-normal"
        >
          <span className="block font-bold text-amber-300 mb-1 flex items-center gap-1">
            <span>📄</span> Physical Document Verification Needed
          </span>
          <span className="block leading-relaxed">{guidanceText}</span>
          <span className="block mt-1 text-[10px] text-slate-400 italic">
            This indicates scan legibility, not legal validity or contractual error.
          </span>
        </span>
      )}
    </span>
  )
}
