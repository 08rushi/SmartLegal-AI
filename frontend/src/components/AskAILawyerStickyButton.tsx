import { Link } from 'react-router-dom'
import AdvocateIcon from './AdvocateIcon'

export default function AskAILawyerStickyButton() {
  return (
    <Link
      to="/advisor"
      aria-label="Ask the AI Legal Advisor"
      className="flex items-center gap-2 rounded-full border border-[#f5c26b]/40 bg-[linear-gradient(180deg,#f5c26b,#cf9b42)] px-4 py-3 text-sm font-semibold text-slate-950 shadow-[0_16px_40px_rgba(245,194,107,0.35)] transition hover:brightness-105"
    >
      <AdvocateIcon className="h-5 w-5" />
      <span className="hidden sm:inline">Ask AI Lawyer</span>
    </Link>
  )
}
