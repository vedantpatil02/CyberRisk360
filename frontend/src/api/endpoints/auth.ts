import { apiClient } from '../client';
import type { LoginResponse } from '../types/auth';

// POST /login expects OAuth2PasswordRequestForm - form-encoded, NOT
// JSON. The form field is literally named "username" but holds the
// user's email (backend/app/api/auth.py).
export async function login(email: string, password: string): Promise<LoginResponse> {
  const body = new URLSearchParams();
  body.set('username', email);
  body.set('password', password);

  const { data } = await apiClient.post<LoginResponse>('/login', body, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });

  return data;
}
