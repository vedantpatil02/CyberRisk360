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
