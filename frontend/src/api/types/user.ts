import type { Role } from './auth';

// GET /users - matches backend/app/schemas/user.py::UserOut exactly.
// Never includes the password hash.
export interface UserAccount {
  id: number;
  username: string;
  email: string;
  role: Role;
  org_id: number;
  is_active: boolean;
  last_login: string | null; // ISO 8601
  created_at: string | null; // ISO 8601
}

// POST /register body - org_slug defaults to "default" server-side when
// omitted.
export interface RegisterInput {
  username: string;
  email: string;
  password: string;
  role: Role;
  org_slug?: string;
}

// Assignable via PATCH /users/{id}/role and the registration form -
// mirrors backend VALID_ROLES (app/services/users/user_service.py),
// which is ALL_ROLES and deliberately excludes super_admin (a
// platform-level role, not an org-assignable one).
export const ASSIGNABLE_ROLES: readonly Role[] = [
  'admin',
  'analyst',
  'pentester',
  'grc_analyst',
  'auditor',
  'manager',
  'ciso',
];
