import { apiClient } from '../client';
import type { DashboardOverview, ExecutiveDashboard, GrcDashboard } from '../types/dashboard';

export async function getOverview(): Promise<DashboardOverview> {
  const { data } = await apiClient.get<DashboardOverview>('/dashboard/overview');
  return data;
}

// GET /dashboard/grc/{framework} and GET /dashboard/executive both use
// require_role(*READ_ROLES) where READ_ROLES = ALL_ROLES - no
// restriction beyond being authenticated, same tier as /reports and
// /audits, so there's no *_READ_ROLES tuple here and no `roles` prop
// needed on their routes/nav items.

export async function getGrcDashboard(frameworkName: string): Promise<GrcDashboard> {
  const { data } = await apiClient.get<GrcDashboard>(`/dashboard/grc/${frameworkName}`);
  return data;
}

export async function getExecutiveDashboard(): Promise<ExecutiveDashboard> {
  const { data } = await apiClient.get<ExecutiveDashboard>('/dashboard/executive');
  return data;
}
