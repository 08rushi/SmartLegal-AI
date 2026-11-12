interface AnalysisProcessingProgressProps {
  stage?: string
  elapsedSeconds?: number
  statusMessage?: string
  onCancel?: () => void
  /** Live server stage (extracting | ocr | analyzing) and 0-100 progress, when the server reports them. */
  jobStage?: string | null
  jobProgress?: number | null
}

const JOB_STAGE_LABEL: Record<string, string> = {
  queued: 'Waiting to start',
  extracting: 'Reading your document',
  ocr: 'Reading scanned / handwritten pages',
  analyzing: 'Analyzing clauses and risks',
}

export function AnalysisProcessingProgress({
  stage = 'processing',
  elapsedSeconds = 0,
  statusMessage,
  onCancel,
  jobStage,
  jobProgress,
}: AnalysisProcessingProgressProps) {
  const hasProgress = typeof jobProgress === 'number' && jobProgress >= 0 && jobProgress <= 100 && Boolean(jobStage)
  const stageLabel = jobStage ? JOB_STAGE_LABEL[jobStage] ?? 'Processing' : null
  const isRetryingProvider = stage === 'retrying_provider'
  const isQueued = stage === 'queued'
  const title = isRetryingProvider
    ? 'Reconnecting to AI Service'
    : isQueued
    ? 'Analysis Queued'
    : 'Analyzing Document'
  const description =
    statusMessage ||
    (isRetryingProvider
      ? 'Retrying analysis after temporary AI provider capacity cooldown. Waiting for next available worker slot.'
      : isQueued
      ? 'Your document is in queue and waiting for an available processing worker.'
      : 'Evaluating clauses against Indian statutory codes (Transfer of Property Act, Indian Contract Act, Registration Act).')

  return (
    <div
      role="status"
      aria-live="polite"
      className="bg-[#121a2d]/90 border border-amber-400/30 p-6 sm:p-8 rounded-3xl backdrop-blur-xl max-w-xl mx-auto space-y-6 text-center animate-fadeIn shadow-2xl"
    >
      {/* Animated Spinner with Amber glow */}
      <div
        className="w-14 h-14 border-4 border-amber-400 border-t-transparent rounded-full animate-spin mx-auto shadow-lg shadow-amber-400/20"
        aria-hidden="true"
      />

      <div className="space-y-2">
        <h3 className="text-xl font-bold text-white tracking-tight">{title}</h3>
        <p className="text-slate-300 text-sm leading-relaxed max-w-md mx-auto">
          {description}
        </p>
      </div>

      {/* Indeterminate Animated Progress Bar */}
      <div className="space-y-2">
        <div
          className="w-full bg-slate-800/80 rounded-full h-2.5 overflow-hidden border border-slate-700/60 relative"
          role="progressbar"
          aria-label="Document analysis in progress"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={hasProgress ? Math.round(jobProgress as number) : undefined}
        >
          {hasProgress ? (
            <div
              className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-amber-500 to-amber-300 transition-all duration-700"
              style={{ width: `${Math.max(4, Math.round(jobProgress as number))}%` }}
            />
          ) : (
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-amber-400 to-transparent w-1/2 rounded-full animate-[pulse_1.5s_ease-in-out_infinite]" />
          )}
        </div>
        <div className="flex items-center justify-between text-xs text-slate-400 font-medium px-1">
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-amber-400 animate-ping" />
            <span>
              {isRetryingProvider
                ? 'Reconnecting'
                : hasProgress && stageLabel
                ? `${stageLabel} — ${Math.round(jobProgress as number)}%`
                : isQueued
                ? 'In Queue'
                : 'Processing'}
            </span>
          </span>
          {elapsedSeconds > 0 && (
            <span className="font-mono text-slate-300">Elapsed: {elapsedSeconds}s</span>
          )}
        </div>
      </div>

      {/* Non-destructive Cancel Action */}
      {onCancel && (
        <div className="pt-2 border-t border-white/5">
          <button
            type="button"
            onClick={onCancel}
            className="inline-flex items-center justify-center min-h-[44px] px-5 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 transition focus:outline-none focus:ring-2 focus:ring-amber-400"
          >
            Cancel Analysis & Return
          </button>
        </div>
      )}
    </div>
  )
}
