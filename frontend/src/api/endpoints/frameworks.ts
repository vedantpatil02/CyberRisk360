import { apiClient } from '../client';
import type { Role } from '../types/auth';
import type { Framework, FrameworkGaps, FrameworkSummary } from '../types/framework';

export const FRAMEWORK_READ_ROLES: readonly Role[] = ['admin', 'analyst', 'auditor'];

export async function listFrameworks(): Promise<Framework[]> {
  const { data } = await apiClient.get<Framework[]>('/frameworks');
  return data;
}

export async function getFrameworkSummary(shortName: string): Promise<FrameworkSummary> {
  const { data } = await apiClient.get<FrameworkSummary>(`/frameworks/${shortName}/summary`);
  return data;
}

export async function getFrameworkGaps(shortName: string): Promise<FrameworkGaps> {
  const { data } = await apiClient.get<FrameworkGaps>(`/frameworks/${shortName}/gaps`);
  return data;
}
