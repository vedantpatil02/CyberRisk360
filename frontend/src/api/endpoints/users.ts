import { apiClient } from '../client';
import type { RegisterInput, UserAccount } from '../types/user';

// GET /users, PATCH /users/{id}/role, /activate, /deactivate,
// /reset-password all use require_role(ROLE_ADMIN) - admin only, not
// the broader WRITE_ROLES group.
export const USER_MANAGEMENT_ROLES = ['admin'] as const;

export async function listUsers(): Promise<UserAccount[]> {
  const { data } = await apiClient.get<UserAccount[]>('/users');
  return data;
}

export async function registerUser(input: RegisterInput): Promise<{ message: string }> {
  const { data } = await apiClient.post<{ message: string }>('/register', input);
  return data;
}

export async function changeOwnPassword(payload: {
  current_password: string;
  new_password: string;
}): Promise<{ message: string }> {
  const { data } = await apiClient.post<{ message: string }>('/users/me/change-password', payload);
  return data;
}

export async function adminResetPassword(
  userId: number,
  newPassword: string,
): Promise<{ message: string }> {
  const { data } = await apiClient.post<{ message: string }>(
    `/users/${userId}/reset-password`,
    { new_password: newPassword },
  );
  return data;
}

export async function deactivateUser(userId: number): Promise<{ message: string }> {
  const { data } = await apiClient.post<{ message: string }>(`/users/${userId}/deactivate`);
  return data;
}

export async function activateUser(userId: number): Promise<{ message: string }> {
  const { data } = await apiClient.post<{ message: string }>(`/users/${userId}/activate`);
  return data;
}

export async function changeUserRole(
  userId: number,
  role: string,
): Promise<{ message: string }> {
  const { data } = await apiClient.patch<{ message: string }>(`/users/${userId}/role`, { role });
  return data;
}
