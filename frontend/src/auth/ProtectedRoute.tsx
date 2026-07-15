import { type ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { AccessDenied } from './AccessDenied';
import { hasRole, type Role } from '../api/types/auth';

interface ProtectedRouteProps {
  children: ReactNode;
  // Omit for "any authenticated user" (e.g. Dashboard, which has no
  // require_role at all on the backend). Provide the exact role tuple
  // a given endpoint actually accepts - RBAC is inconsistent across
  // this backend, so there is no single generic "read role" tier to
  // default to.
  roles?: readonly Role[];
}

export function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!hasRole(user.role, roles)) {
    return <AccessDenied currentRole={user.role} requiredRoles={roles ?? []} />;
  }

  return <>{children}</>;
}
