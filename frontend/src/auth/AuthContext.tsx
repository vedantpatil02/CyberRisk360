import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
import { authStorage } from './authStorage';
import type { JwtPayload, Role } from '../api/types/auth';

interface AuthUser {
  email: string;
  role: Role;
  orgId: number;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function toAuthUser(payload: JwtPayload): AuthUser {
  return { email: payload.sub, role: payload.role, orgId: payload.org_id };
}

function readInitialUser(): AuthUser | null {
  const token = authStorage.getToken();
  if (!token) return null;

  const payload = authStorage.decode(token);
  if (!payload || authStorage.isExpired(payload)) {
    authStorage.clear();
    return null;
  }

  return toAuthUser(payload);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(readInitialUser);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      login: (token: string) => {
        authStorage.setToken(token);
        const payload = authStorage.decode(token);
        setUser(payload ? toAuthUser(payload) : null);
      },
      // The entire logout implementation: there is no server-side
      // session to invalidate (no /logout endpoint, no token
      // blacklist - backend/app/api/auth.py), so discarding the
      // client-side token is genuinely all that's required.
      logout: () => {
        authStorage.clear();
        setUser(null);
      },
    }),
    [user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
