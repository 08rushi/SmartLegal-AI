import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import AdvocateIcon from './AdvocateIcon'

export default function AskAILawyerStickyButton() {
  const { t } = useTranslation('shell')
  return (
    <Link
      to="/advisor"
      aria-label={t('floating.askAiAria')}
      className="flex items-center gap-2 rounded-full border border-[#f5c26b]/40 bg-[linear-gradient(180deg,#f5c26b,#cf9b42)] px-4 py-3 text-sm font-semibold text-slate-950 shadow-[0_16px_40px_rgba(245,194,107,0.35)] transition hover:brightness-105"
    >
      <AdvocateIcon className="h-5 w-5" />
      <span className="hidden sm:inline">{t('floating.askAi')}</span>
    </Link>
  )
}
