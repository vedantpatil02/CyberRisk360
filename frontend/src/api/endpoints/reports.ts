import { apiClient } from '../client';
import type { ComplianceReport, ExecutiveReport, TechnicalReport } from '../types/report';

// All three /reports/* routes use require_role(*READ_ROLES) where
// READ_ROLES = ALL_ROLES (backend/app/core/constants.py) - no
// restriction beyond being authenticated, same tier as GET /assets and
// GET /dashboard/overview, so there's no *_READ_ROLES tuple to export
// here and no `roles` prop needed on their routes/nav item.

export async function getExecutiveReport(): Promise<ExecutiveReport> {
  const { data } = await apiClient.get<ExecutiveReport>('/reports/executive');
  return data;
}

export async function getTechnicalReport(): Promise<TechnicalReport> {
  const { data } = await apiClient.get<TechnicalReport>('/reports/technical');
  return data;
}

export async function getComplianceReport(shortName: string): Promise<ComplianceReport> {
  const { data } = await apiClient.get<ComplianceReport>(`/reports/compliance/${shortName}`);
  return data;
}

// Fetches the PDF as a blob and saves it via a synthetic link click -
// a plain <a href> to the API wouldn't carry the Bearer token that
// apiClient's interceptor injects, so the download has to go through
// an authenticated axios request first.
export async function downloadReportPdf(path: string, filename: string): Promise<void> {
  const response = await apiClient.get<Blob>(path, {
    params: { format: 'pdf' },
    responseType: 'blob',
  });

  const url = window.URL.createObjectURL(response.data);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
