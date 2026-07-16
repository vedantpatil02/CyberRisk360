import { apiClient } from '../client';
import type { Notification } from '../types/notification';

// GET /notifications has no role check beyond authentication
// (READ_ROLES = every org role) - same tier as Dashboard/Reports, so
// no role-tuple constant needed.

export async function listNotifications(): Promise<Notification[]> {
  const { data } = await apiClient.get<Notification[]>('/notifications');
  return data;
}
