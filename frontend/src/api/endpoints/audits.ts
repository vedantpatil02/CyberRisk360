import { apiClient } from '../client';
import type { Role } from '../types/auth';
import type {
  Audit,
  AuditCreateInput,
  AuditFinding,
  AuditFindingCreateInput,
  AuditFindingUpdateInput,
  AuditListParams,
  AuditUpdateInput,
} from '../types/audit';

// GET /audits and GET /audits/{id} both use require_role(*READ_ROLES)
// on the backend (= ALL_ROLES, no restriction beyond authentication) -
// same tier as Reports/Dashboard, so no roles prop needed on their
// routes/nav item, and no *_READ_ROLES constant to export here.

// POST/PUT/PATCH-close/findings-write all require OVERSIGHT_ROLES -
// audits are fundamentally an oversight function, same reasoning
// already applied to Risk Treatment approval.
export const AUDIT_WRITE_ROLES: readonly Role[] = ['admin', 'auditor', 'ciso', 'manager'];

export async function listAudits(params: AuditListParams): Promise<Audit[]> {
  const { data } = await apiClient.get<Audit[]>('/audits', { params });
  return data;
}

export async function getAudit(id: number): Promise<Audit> {
  const { data } = await apiClient.get<Audit>(`/audits/${id}`);
  return data;
}

export async function createAudit(input: AuditCreateInput): Promise<Audit> {
  const { data } = await apiClient.post<Audit>('/audits', input);
  return data;
}

export async function updateAudit(id: number, input: AuditUpdateInput): Promise<Audit> {
  const { data } = await apiClient.put<Audit>(`/audits/${id}`, input);
  return data;
}

export async function closeAudit(id: number): Promise<Audit> {
  const { data } = await apiClient.patch<Audit>(`/audits/${id}/close`);
  return data;
}

export async function listAuditFindings(auditId: number): Promise<AuditFinding[]> {
  const { data } = await apiClient.get<AuditFinding[]>(`/audits/${auditId}/findings`);
  return data;
}

export async function createAuditFinding(
  auditId: number,
  input: AuditFindingCreateInput,
): Promise<AuditFinding> {
  const { data } = await apiClient.post<AuditFinding>(`/audits/${auditId}/findings`, input);
  return data;
}

export async function updateAuditFinding(
  findingId: number,
  input: AuditFindingUpdateInput,
): Promise<AuditFinding> {
  const { data } = await apiClient.put<AuditFinding>(`/findings/${findingId}`, input);
  return data;
}
