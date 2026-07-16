import { apiClient } from '../client';
import type { Role } from '../types/auth';
import type { ImportResult } from '../types/importReport';

// POST /imports/nessus_report_upload uses require_role(ROLE_ADMIN,
// ROLE_ANALYST) - matches backend/app/api/imports.py exactly.
export const IMPORT_WRITE_ROLES: readonly Role[] = ['admin', 'analyst'];

export async function uploadReport(file: File): Promise<ImportResult> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await apiClient.post<ImportResult>('/imports/nessus_report_upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}
