interface StatusBadgeProps {
  status: string
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const normalized = status.toLowerCase()

  let style = 'bg-slate-800 text-slate-300 border-slate-700'
  let label = status

  if (normalized === 'completed' || normalized === 'ready' || normalized === 'received') {
    style = 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
    label = 'Completed'
  } else if (normalized === 'in_progress' || normalized === 'processing' || normalized === 'submitted') {
    style = 'bg-amber-500/10 text-amber-300 border-amber-500/20 animate-pulse'
    label = 'In Progress'
  } else if (normalized === 'error' || normalized === 'failed') {
    style = 'bg-rose-500/10 text-rose-300 border-rose-500/20'
    label = 'Failed'
  }

  return (
    <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${style}`}>
      {label}
    </span>
  )
}
