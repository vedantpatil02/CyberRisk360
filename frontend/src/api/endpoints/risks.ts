import { apiClient } from '../client';
import type { Role } from '../types/auth';
import type { Risk, RiskListParams } from '../types/risk';

// GET /risks and GET /risks/{id} both require this tuple (unlike
// Assets, list and detail sit at the same RBAC tier here).
export const RISK_READ_ROLES: readonly Role[] = ['admin', 'analyst', 'auditor'];

export async function listRisks(params: RiskListParams): Promise<Risk[]> {
  const { data } = await apiClient.get<Risk[]>('/risks', { params });
  return data;
}

export async function getRisk(id: number): Promise<Risk> {
  const { data } = await apiClient.get<Risk>(`/risks/${id}`);
  return data;
}
