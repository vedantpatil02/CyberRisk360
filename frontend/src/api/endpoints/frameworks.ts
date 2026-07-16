import { apiClient } from '../client';
import type { Role } from '../types/auth';
import type {
  Framework,
  FrameworkCreateInput,
  FrameworkGaps,
  FrameworkSummary,
  FrameworkUpdateInput,
} from '../types/framework';

export const FRAMEWORK_READ_ROLES: readonly Role[] = ['admin', 'analyst', 'auditor'];

// POST/PATCH/DELETE /frameworks are all admin-only on the backend -
// the tightest write tier of any resource in this app.
export const FRAMEWORK_WRITE_ROLES: readonly Role[] = ['admin'];

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

// Returns the full created Framework directly.
export async function createFramework(input: FrameworkCreateInput): Promise<Framework> {
  const { data } = await apiClient.post<Framework>('/frameworks', input);
  return data;
}

// Returns the full updated Framework directly.
export async function updateFramework(
  id: number,
  input: FrameworkUpdateInput,
): Promise<Framework> {
  const { data } = await apiClient.patch<Framework>(`/frameworks/${id}`, input);
  return data;
}

export async function deleteFramework(id: number): Promise<{ message: string }> {
  const { data } = await apiClient.delete<{ message: string }>(`/frameworks/${id}`);
  return data;
}
