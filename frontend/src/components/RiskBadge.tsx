import { useTranslation } from 'react-i18next'
import type { RiskLevel } from '../types'

interface Props {
  level: RiskLevel
  score?: number
}

const config = {
  high: {
    className: 'risk-badge-high',
    dot: 'bg-[#fb7185]',
  },
  medium: {
    className: 'risk-badge-medium',
    dot: 'bg-[#f5c26b]',
  },
  low: {
    className: 'risk-badge-low',
    dot: 'bg-[#34d399]',
  },
}

export default function RiskBadge({ level, score }: Props) {
  const { t } = useTranslation('clauses')
  const { className, dot } = config[level] ?? config.medium

  return (
    <span className={className}>
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${dot}`} />
      <span>{t(`risk.${level}`, { defaultValue: String(level) })}</span>
      {score !== undefined && <span className="opacity-70">{t('score', { score })}</span>}
    </span>
  )
}
