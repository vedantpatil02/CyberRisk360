import { apiClient } from '../client';
import type { Role } from '../types/auth';
import type {
  Risk,
  RiskCreateInput,
  RiskListParams,
  RiskTreatmentHistoryEntry,
  RiskUpdateInput,
  TreatmentType,
} from '../types/risk';

// GET /risks and GET /risks/{id} both require this tuple (unlike
// Assets, list and detail sit at the same RBAC tier here).
export const RISK_READ_ROLES: readonly Role[] = ['admin', 'analyst', 'auditor'];

// POST/PUT/PATCH-close all hard-code this same pair on the backend.
export const RISK_WRITE_ROLES: readonly Role[] = ['admin', 'analyst'];

// POST /risks/{id}/treatment requires COMPLIANCE_ROLES on the backend.
export const RISK_TREATMENT_PROPOSE_ROLES: readonly Role[] = ['admin', 'analyst', 'grc_analyst'];

// PATCH /risks/{id}/treatment/{approve,reject} requires OVERSIGHT_ROLES -
// deliberately a different tier than propose (separation of duties).
export const RISK_TREATMENT_APPROVE_ROLES: readonly Role[] = [
  'admin',
  'auditor',
  'ciso',
  'manager',
];

export async function listRisks(params: RiskListParams): Promise<Risk[]> {
  const { data } = await apiClient.get<Risk[]>('/risks', { params });
  return data;
}

export async function getRisk(id: number): Promise<Risk> {
  const { data } = await apiClient.get<Risk>(`/risks/${id}`);
  return data;
}

// Returns {message, score, level} - the backend doesn't return the
// created record itself, only a confirmation + the server-computed
// score/level.
export async function createRisk(
  input: RiskCreateInput,
): Promise<{ message: string; score: number; level: string }> {
  const { data } = await apiClient.post<{ message: string; score: number; level: string }>(
    '/risks',
    input,
  );
  return data;
}

// Returns {message} only (not the updated record) - matches the
// backend's PUT /risks/{id} response exactly.
export async function updateRisk(
  id: number,
  input: RiskUpdateInput,
): Promise<{ message: string }> {
  const { data } = await apiClient.put<{ message: string }>(`/risks/${id}`, input);
  return data;
}

export async function closeRisk(id: number): Promise<{ message: string }> {
  const { data } = await apiClient.patch<{ message: string }>(`/risks/${id}/close`);
  return data;
}

export async function proposeTreatment(
  id: number,
  body: { treatment_type: TreatmentType; justification: string },
): Promise<Risk> {
  const { data } = await apiClient.post<Risk>(`/risks/${id}/treatment`, body);
  return data;
}

export async function approveTreatment(id: number, note?: string): Promise<Risk> {
  const { data } = await apiClient.patch<Risk>(`/risks/${id}/treatment/approve`, { note });
  return data;
}

export async function rejectTreatment(id: number, note?: string): Promise<Risk> {
  const { data } = await apiClient.patch<Risk>(`/risks/${id}/treatment/reject`, { note });
  return data;
}

export async function getTreatmentHistory(id: number): Promise<RiskTreatmentHistoryEntry[]> {
  const { data } = await apiClient.get<RiskTreatmentHistoryEntry[]>(
    `/risks/${id}/treatment/history`,
  );
  return data;
}
