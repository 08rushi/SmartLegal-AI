import { useTranslation } from 'react-i18next'
import { useAppSelector } from '../hooks/redux'
import LoginRequired from './LoginRequired'

interface ProtectedRouteProps {
  children: React.ReactNode
  /** Optional tailored prompt shown when the user is not signed in. */
  title?: string
  message?: string
  /** i18n keys (e.g. 'shell:protected.upload.title'); translated at render so they follow the language. */
  titleKey?: string
  messageKey?: string
}

/**
 * Wraps routes that require authentication. When there is no signed-in session we show a
 * friendly "please sign in" prompt (which remembers where the user was going)
 * instead of hard-redirecting — no jarring full-page navigation.
 */
export default function ProtectedRoute({ children, title, message, titleKey, messageKey }: ProtectedRouteProps) {
  const { t } = useTranslation()
  const { isAuthenticated, sessionChecked } = useAppSelector((s) => s.auth)

  // Cookie session is still being restored (GET /auth/me): render nothing rather than flashing "sign in".
  if (!sessionChecked) return null

  if (!isAuthenticated) {
    return (
      <LoginRequired
        title={title ?? (titleKey ? t(titleKey) : undefined)}
        message={message ?? (messageKey ? t(messageKey) : undefined)}
      />
    )
  }

  return <>{children}</>
}
