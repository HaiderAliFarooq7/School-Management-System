import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export function ProtectedRoute({ allowedRoles }: { allowedRoles?: string[] }) {
  const { isAuthenticated, role } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    // Remember where the user was headed so login can send them straight
    // there — e.g. scanning a fee-challan QR with a phone camera opens
    // /fees/student/<id>, and after signing in that exact page loads.
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  }
  if (allowedRoles && role && !allowedRoles.includes(role)) {
    return <Navigate to="/" replace />
  }
  return <Outlet />
}
