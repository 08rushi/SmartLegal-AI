import type { RiskLevel } from '../types'

interface Props {
  level: RiskLevel
  score?: number
}

const config = {
  high: {
    label: 'High Risk',
    className: 'risk-badge-high',
    dot: 'bg-red-500',
  },
  medium: {
    label: 'Medium Risk',
    className: 'risk-badge-medium',
    dot: 'bg-amber-500',
  },
  low: {
    label: 'Low Risk',
    className: 'risk-badge-low',
    dot: 'bg-green-500',
  },
}

export default function RiskBadge({ level, score }: Props) {
  const { label, className, dot } = config[level]
  return (
    <span className={className}>
      <span className={`w-1.5 h-1.5 rounded-full ${dot} inline-block`} />
      {label}
      {score !== undefined && (
        <span className="ml-1 opacity-70">({score}/10)</span>
      )}
    </span>
  )
}
