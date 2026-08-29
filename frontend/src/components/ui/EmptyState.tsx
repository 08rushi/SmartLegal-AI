interface EmptyStateProps {

  icon?: string
  title: string
  description?: string
  actionLabel?: string
  onAction?: () => void
}

export function EmptyState({
  icon = '📭',
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="bg-[#121a2d]/80 border border-slate-800 rounded-3xl p-10 text-center space-y-4 max-w-lg mx-auto backdrop-blur-xl">
      <div className="text-5xl">{icon}</div>
      <h3 className="text-xl font-bold text-white">{title}</h3>
      {description && <p className="text-slate-400 text-sm leading-relaxed">{description}</p>}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="mt-4 px-6 py-3 bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold text-sm rounded-xl transition-all shadow-lg shadow-amber-400/20"
        >
          {actionLabel}
        </button>
      )}
    </div>
  )
}
