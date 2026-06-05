import { Navigate } from 'react-router-dom'
import { useAppSelector } from '../hooks/redux'

interface ProtectedRouteProps {
  children: React.ReactNode
}

/**
 * Wraps routes that require authentication.
 * Redirects to /login if no valid JWT token is present.
 */
export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { token } = useAppSelector((s) => s.auth)

  if (!token) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
