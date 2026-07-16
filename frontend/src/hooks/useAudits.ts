import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { listAudits } from '../api/endpoints/audits';
import type { AuditListParams } from '../api/types/audit';

export function useAudits(params: AuditListParams) {
  return useQuery({
    queryKey: ['audits', params],
    queryFn: () => listAudits(params),
    placeholderData: keepPreviousData,
  });
}
