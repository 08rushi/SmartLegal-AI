import type { RiskLevel } from '../types'

interface Props {
  level: RiskLevel
  score?: number
}

const config = {
  high: {
    label: 'High Risk',
    className: 'risk-badge-high',
    dot: 'bg-[#fb7185]',
  },
  medium: {
    label: 'Medium Risk',
    className: 'risk-badge-medium',
    dot: 'bg-[#f5c26b]',
  },
  low: {
    label: 'Low Risk',
    className: 'risk-badge-low',
    dot: 'bg-[#34d399]',
  },
}

export default function RiskBadge({ level, score }: Props) {
  const { label, className, dot } = config[level]

  return (
    <span className={className}>
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${dot}`} />
      <span>{label}</span>
      {score !== undefined && <span className="opacity-70">({score}/10)</span>}
    </span>
  )
}
