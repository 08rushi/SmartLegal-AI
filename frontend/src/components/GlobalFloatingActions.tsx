import { useLocation } from 'react-router-dom'
import WhatsAppStickyButton from './WhatsAppStickyButton'
import AskAILawyerStickyButton from './AskAILawyerStickyButton'

const EXCLUDED_PATHS = [
  '/advisor',
  '/channels/whatsapp',
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
]

export default function GlobalFloatingActions() {
  const location = useLocation()
  const isExcluded = EXCLUDED_PATHS.includes(location.pathname)

  if (isExcluded) {
    return null
  }

  return (
    <div
      data-testid="global-floating-actions"
      className="fixed bottom-5 right-5 z-40 flex flex-col items-end gap-3 pb-[env(safe-area-inset-bottom)] pr-[env(safe-area-inset-right)] sm:bottom-6 sm:right-6"
    >
      <WhatsAppStickyButton />
      <AskAILawyerStickyButton />
    </div>
  )
}
