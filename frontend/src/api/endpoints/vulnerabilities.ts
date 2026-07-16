import { apiClient } from '../client';
import type { Role } from '../types/auth';
import type {
  CweInfo,
  EpssScore,
  ExploitDbEntry,
  KevStatus,
  Vulnerability,
  VulnerabilityControlSummary,
  VulnerabilityCreateInput,
  VulnerabilityListParams,
  VulnerabilityUpdateInput,
} from '../types/vulnerability';

// The exact role tuple backend/app/api/vulnerabilities.py's
// require_role(...) accepts for every GET on this resource. NOT named
// READ_ROLES - the backend's own READ_ROLES constant means something
// broader (all 7 org roles, used by /dashboard/grc, /reports,
// evidence) and reusing that name here would misrepresent what this
// resource actually allows.
export const VULNERABILITY_READ_ROLES: readonly Role[] = ['admin', 'analyst', 'auditor'];

// POST/PUT/PATCH-close all hard-code this same pair on the backend
// (not the broader WRITE_ROLES group, which would also include
// pentester - pentesters can upload evidence/trigger CVE enrichment
// but cannot create, edit, or close a vulnerability record itself).
export const VULNERABILITY_WRITE_ROLES: readonly Role[] = ['admin', 'analyst'];

export async function listVulnerabilities(
  params: VulnerabilityListParams,
): Promise<Vulnerability[]> {
  const { data } = await apiClient.get<Vulnerability[]>('/vulnerabilities', { params });
  return data;
}

export async function getVulnerability(id: number): Promise<Vulnerability> {
  const { data } = await apiClient.get<Vulnerability>(`/vulnerabilities/${id}`);
  return data;
}

export async function getVulnerabilityControls(id: number): Promise<VulnerabilityControlSummary[]> {
  const { data } = await apiClient.get<VulnerabilityControlSummary[]>(
    `/vulnerabilities/${id}/controls`,
  );
  return data;
}

export async function getKevStatus(id: number): Promise<KevStatus> {
  const { data } = await apiClient.get<KevStatus>(`/vulnerabilities/${id}/kev-status`);
  return data;
}

export async function getEpssScore(id: number): Promise<EpssScore> {
  const { data } = await apiClient.get<EpssScore>(`/vulnerabilities/${id}/epss-score`);
  return data;
}

export async function getCweInfo(id: number): Promise<CweInfo> {
  const { data } = await apiClient.get<CweInfo>(`/vulnerabilities/${id}/cwe-info`);
  return data;
}

export async function getExploits(id: number): Promise<ExploitDbEntry[]> {
  const { data } = await apiClient.get<ExploitDbEntry[]>(`/vulnerabilities/${id}/exploits`);
  return data;
}

// Returns {message, severity} - the backend doesn't return the created
// record itself, only a confirmation + the server-computed severity.
export async function createVulnerability(
  input: VulnerabilityCreateInput,
): Promise<{ message: string; severity: string }> {
  const { data } = await apiClient.post<{ message: string; severity: string }>(
    '/vulnerabilities',
    input,
  );
  return data;
}

// Returns {message} only (not the updated record) - matches the
// backend's PUT /vulnerabilities/{id} response exactly.
export async function updateVulnerability(
  id: number,
  input: VulnerabilityUpdateInput,
): Promise<{ message: string }> {
  const { data } = await apiClient.put<{ message: string }>(`/vulnerabilities/${id}`, input);
  return data;
}

export async function closeVulnerability(id: number): Promise<{ message: string }> {
  const { data } = await apiClient.patch<{ message: string }>(`/vulnerabilities/${id}/close`);
  return data;
}
