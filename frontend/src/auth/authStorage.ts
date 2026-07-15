import { jwtDecode } from 'jwt-decode';
import type { JwtPayload } from '../api/types/auth';

// sessionStorage, not localStorage: there is no refresh-token endpoint
// (backend/app/api/auth.py) and the token has a fixed 60-minute expiry,
// so nothing is gained by surviving a browser restart - an expired
// token just fails on first use. sessionStorage still survives
// in-tab refresh/navigation (normal usage within the window) but
// clears when the tab closes, so no stale tokens accumulate.
const TOKEN_KEY = 'cyberrisk360.token';

function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

function setToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

function clear(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}

// GET /me returns nothing this decode doesn't already give you for
// free, offline (backend/app/api/auth.py::get_me just returns the
// decoded JWT payload verbatim) - decode client-side instead.
function decode(token: string): JwtPayload | null {
  try {
    return jwtDecode<JwtPayload>(token);
  } catch {
    return null;
  }
}

function isExpired(payload: JwtPayload): boolean {
  return payload.exp * 1000 <= Date.now();
}

export const authStorage = {
  getToken,
  setToken,
  clear,
  decode,
  isExpired,
};
