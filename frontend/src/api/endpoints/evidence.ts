import { apiClient } from '../client';
import type { Role } from '../types/auth';
import type { EvidenceAttachment } from '../types/evidence';

// POST/GET .../evidence and DELETE /evidence/{id} all use the
// backend's generic WRITE_ROLES/READ_ROLES groups (app/core/
// constants.py), NOT the narrower per-resource *_WRITE_ROLES tuples -
// WRITE_ROLES also includes pentester, who can attach remediation
// evidence without being able to create/edit the vulnerability or risk
// itself.
export const EVIDENCE_WRITE_ROLES: readonly Role[] = ['admin', 'analyst', 'pentester'];
export const EVIDENCE_READ_ROLES: readonly Role[] = [
  'admin',
  'analyst',
  'pentester',
  'grc_analyst',
  'auditor',
  'manager',
  'ciso',
];

export async function listVulnerabilityEvidence(
  vulnerabilityId: number,
): Promise<EvidenceAttachment[]> {
  const { data } = await apiClient.get<EvidenceAttachment[]>(
    `/vulnerabilities/${vulnerabilityId}/evidence`,
  );
  return data;
}

export async function listRiskEvidence(riskId: number): Promise<EvidenceAttachment[]> {
  const { data } = await apiClient.get<EvidenceAttachment[]>(`/risks/${riskId}/evidence`);
  return data;
}

async function uploadEvidence(
  path: string,
  file: File,
  expiresAt: string | null,
): Promise<EvidenceAttachment> {
  const form = new FormData();
  form.append('file', file);
  if (expiresAt) {
    form.append('expires_at', expiresAt);
  }
  const { data } = await apiClient.post<EvidenceAttachment>(path, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export function uploadVulnerabilityEvidence(
  vulnerabilityId: number,
  file: File,
  expiresAt: string | null,
): Promise<EvidenceAttachment> {
  return uploadEvidence(`/vulnerabilities/${vulnerabilityId}/evidence`, file, expiresAt);
}

export function uploadRiskEvidence(
  riskId: number,
  file: File,
  expiresAt: string | null,
): Promise<EvidenceAttachment> {
  return uploadEvidence(`/risks/${riskId}/evidence`, file, expiresAt);
}

// Fetches the file as a blob and saves it via a synthetic link click -
// same technique as api/endpoints/reports.ts::downloadReportPdf, since
// a plain <a href> can't carry the Bearer token apiClient's interceptor
// injects.
export async function downloadEvidence(attachment: EvidenceAttachment): Promise<void> {
  const response = await apiClient.get<Blob>(`/evidence/${attachment.id}/download`, {
    responseType: 'blob',
  });

  const url = window.URL.createObjectURL(response.data);
  const link = document.createElement('a');
  link.href = url;
  link.download = attachment.file_name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export async function deleteEvidence(attachmentId: number): Promise<{ message: string }> {
  const { data } = await apiClient.delete<{ message: string }>(`/evidence/${attachmentId}`);
  return data;
}
