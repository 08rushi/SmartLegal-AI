import { useTranslation } from 'react-i18next'
import { Icon, type IconName } from './Icon'

export type RiskLevelName = 'high' | 'medium' | 'low'

interface RiskPillProps {
  level: RiskLevelName | string
  /** Optional 0-10 score, shown as "(7/10)". */
  score?: number
  /** `short` shows "High" instead of "High Risk". */
  short?: boolean
  className?: string
}

// Colour is never the only signal: each level has its own icon shape AND a word.
const CONFIG: Record<RiskLevelName, { cls: string; icon: IconName }> = {
  high: { cls: 'border-danger-line bg-danger-bg text-danger', icon: 'warning' },
  medium: { cls: 'border-warn-line bg-warn-bg text-warn', icon: 'alert' },
  low: { cls: 'border-ok-line bg-ok-bg text-ok', icon: 'check' },
}

/** Risk level as icon + word (+ score). High = ⚠, Medium = ❗, Low = ✅. */
export function RiskPill({ level, score, short = false, className = '' }: RiskPillProps) {
  const { t } = useTranslation('clauses')
  const key = (level in CONFIG ? level : 'medium') as RiskLevelName
  const { cls, icon } = CONFIG[key]
  // Fall back to the raw value if the backend sends an unexpected level.
  const word = t(`${short ? 'riskShort' : 'risk'}.${level}`, { defaultValue: String(level) })
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${cls} ${className}`}>
      <Icon name={icon} size={14} />
      <span>{word}</span>
      {score !== undefined && <span className="font-medium opacity-90">{t('score', { score })}</span>}
    </span>
  )
}

export default RiskPill
