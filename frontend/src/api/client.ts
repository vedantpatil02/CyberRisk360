import axios from 'axios';
import { authStorage } from '../auth/authStorage';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const apiClient = axios.create({ baseURL: API_BASE_URL });

apiClient.interceptors.request.use((config) => {
  const token = authStorage.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    // decode_access_token (backend/app/services/auth/auth.py) catches
    // JWTError broadly, so a missing, malformed, invalid, AND expired
    // token all collapse to the same 401 from get_current_user - 401
    // always means "the session is dead," so this is the one safe
    // place to clear it and force a re-login.
    //
    // 403 is deliberately NOT handled here: require_role() raises 403
    // for a valid, non-expired token that simply lacks permission for
    // one endpoint (e.g. a pentester hitting GET /vulnerabilities) -
    // logging that user out would be wrong. Callers handle 403
    // per-page (see ProtectedRoute / AccessDenied).
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      authStorage.clear();
      if (window.location.pathname !== '/login') {
        window.location.assign('/login');
      }
    }
    return Promise.reject(error);
  },
);
