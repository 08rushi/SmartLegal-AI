import { useAppSelector } from '../hooks/redux'
import LoginRequired from './LoginRequired'

interface ProtectedRouteProps {
  children: React.ReactNode
  /** Optional tailored prompt shown when the user is not signed in. */
  title?: string
  message?: string
}

/**
 * Wraps routes that require authentication. When there is no token we show a
 * friendly "please sign in" prompt (which remembers where the user was going)
 * instead of hard-redirecting — no jarring full-page navigation.
 */
export default function ProtectedRoute({ children, title, message }: ProtectedRouteProps) {
  const { token } = useAppSelector((s) => s.auth)

  if (!token) {
    return <LoginRequired title={title} message={message} />
  }

  return <>{children}</>
}
