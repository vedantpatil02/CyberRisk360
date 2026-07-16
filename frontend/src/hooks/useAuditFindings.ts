import { useQuery } from '@tanstack/react-query';
import { listAuditFindings } from '../api/endpoints/audits';

export function useAuditFindings(auditId: number) {
  return useQuery({
    queryKey: ['audits', auditId, 'findings'],
    queryFn: () => listAuditFindings(auditId),
  });
}
