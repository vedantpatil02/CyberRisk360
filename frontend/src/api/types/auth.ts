// Mirrors backend/app/core/constants.py's role values exactly.
export type Role =
  | 'admin'
  | 'analyst'
  | 'pentester'
  | 'grc_analyst'
  | 'auditor'
  | 'manager'
  | 'ciso'
  | 'super_admin';

// The JWT payload backend/app/services/auth/auth.py::create_access_token
// encodes at login - GET /me returns exactly this, nothing more, so
// there's no need to call it separately once the token is decoded.
export interface JwtPayload {
  sub: string; // email
  role: Role;
  org_id: number;
  exp: number; // unix seconds
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

// Mirrors backend/app/dependencies/rbac.py::require_role, which
// special-cases super_admin to bypass every role check regardless of
// the endpoint's allowed-roles tuple - a platform super-admin spans
// every capability, not just organization management. Every
// role-gated check on the frontend (ProtectedRoute, nav visibility)
// should go through this instead of a raw `roles.includes(...)`.
export function hasRole(role: Role, allowedRoles?: readonly Role[]): boolean {
  if (role === 'super_admin') return true;
  if (!allowedRoles) return true; // no restriction = any authenticated role
  return allowedRoles.includes(role);
}
