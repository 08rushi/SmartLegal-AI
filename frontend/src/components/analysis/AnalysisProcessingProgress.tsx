interface AnalysisProcessingProgressProps {
  stage: string
  progressPct: number
  statusMessage?: string
}

export function AnalysisProcessingProgress({
  stage,
  progressPct,
  statusMessage,
}: AnalysisProcessingProgressProps) {
  const stageLabels: Record<string, string> = {
    queued: '⏳ Job Queued in Queue',
    extracting: '📄 Extracting PyMuPDF Text & Page Structure...',
    ocr: '🔍 Performing Tesseract OCR Scan...',
    analyzing: '🧠 AI Legal Engine Analyzing Clauses & Indian Law Violations...',
    completed: '✅ Analysis Complete!',
    failed: '❌ Processing Failed',
  }

  return (
    <div className="bg-[#121a2d]/90 border border-amber-400/30 p-8 rounded-3xl backdrop-blur-xl max-w-xl mx-auto space-y-6 text-center animate-fadeIn shadow-2xl">
      <div className="w-16 h-16 border-4 border-amber-400 border-t-transparent rounded-full animate-spin mx-auto shadow-lg shadow-amber-400/20" />

      <div className="space-y-2">
        <h3 className="text-xl font-bold text-white">
          {stageLabels[stage] || 'Processing Legal Document...'}
        </h3>
        <p className="text-slate-400 text-sm">
          {statusMessage || 'Our dual LLM pipeline is evaluating clauses against Indian statutory codes.'}
        </p>
      </div>

      {/* Real Progress Bar */}
      <div className="space-y-2">
        <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden border border-slate-700">
          <div
            className="bg-gradient-to-r from-amber-400 to-amber-500 h-full transition-all duration-500 rounded-full"
            style={{ width: `${Math.max(5, progressPct)}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-slate-400 font-medium">
          <span>Stage: {stage.toUpperCase()}</span>
          <span className="text-amber-400 font-bold">{progressPct}%</span>
        </div>
      </div>
    </div>
  )
}
