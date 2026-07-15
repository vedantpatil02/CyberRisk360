import { apiClient } from '../client';
import type { Role } from '../types/auth';
import type {
  Vulnerability,
  VulnerabilityControlSummary,
  VulnerabilityListParams,
} from '../types/vulnerability';

// The exact role tuple backend/app/api/vulnerabilities.py's
// require_role(...) accepts for every GET on this resource. NOT named
// READ_ROLES - the backend's own READ_ROLES constant means something
// broader (all 7 org roles, used by /dashboard/grc, /reports,
// evidence) and reusing that name here would misrepresent what this
// resource actually allows.
export const VULNERABILITY_READ_ROLES: readonly Role[] = ['admin', 'analyst', 'auditor'];

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
