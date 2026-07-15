import { apiClient } from '../client';
import type { DashboardOverview } from '../types/dashboard';

export async function getOverview(): Promise<DashboardOverview> {
  const { data } = await apiClient.get<DashboardOverview>('/dashboard/overview');
  return data;
}
