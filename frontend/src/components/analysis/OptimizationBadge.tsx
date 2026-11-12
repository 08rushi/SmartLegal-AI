import { useState } from 'react'
import type { OptimizationTelemetryInfo } from '../../types'

interface OptimizationBadgeProps {
  optimization?: OptimizationTelemetryInfo
}

function formatBytes(bytes?: number): string {
  if (!bytes || bytes <= 0) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function OptimizationBadge({ optimization }: OptimizationBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false)

  if (!optimization || !optimization.optimization_applied) {
    return null
  }

  const origStr = formatBytes(optimization.original_size_bytes)
  const optStr = formatBytes(optimization.optimized_size_bytes)
  const reductionPct = optimization.compression_ratio
    ? Math.round((1 - optimization.compression_ratio) * 100)
    : optimization.original_size_bytes && optimization.optimized_size_bytes
    ? Math.round(
        (1 - optimization.optimized_size_bytes / optimization.original_size_bytes) * 100
      )
    : 0

  return (
    <div className="relative inline-block align-middle">
      <button
        type="button"
        onClick={() => setShowTooltip((p) => !p)}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onFocus={() => setShowTooltip(true)}
        onBlur={() => setShowTooltip(false)}
        aria-label={`Document was automatically optimized. Reduced from ${origStr} to ${optStr} (${reductionPct}% smaller).`}
        aria-expanded={showTooltip}
        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-semibold hover:bg-emerald-500/15 focus:outline-none focus:ring-2 focus:ring-emerald-400 transition"
      >
        <span aria-hidden="true">⚡</span>
        <span>
          Optimized: {origStr} → {optStr}
          {reductionPct > 0 && ` (${reductionPct}% smaller)`}
        </span>
      </button>

      {showTooltip && (
        <div
          role="tooltip"
          className="absolute z-50 top-full left-0 mt-2 w-72 p-3 rounded-2xl bg-slate-900/95 border border-emerald-500/30 text-xs text-slate-200 shadow-2xl backdrop-blur-md animate-fadeIn"
        >
          <div className="font-bold text-emerald-300 mb-1 flex items-center gap-1.5">
            <span>⚡</span> Adaptive Document Optimization
          </div>
          <p className="text-slate-300 leading-relaxed">
            Your file was automatically compressed to ensure fast AI analysis while preserving 100% of text and visual legibility.
          </p>
          {optimization.pages_split > 0 && (
            <p className="mt-1 text-[11px] text-amber-300 font-medium">
              📄 Multi-page document was processed in parallel segments.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
