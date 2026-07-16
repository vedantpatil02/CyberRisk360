import { useQuery } from '@tanstack/react-query';
import { getAudit } from '../api/endpoints/audits';

export function useAudit(id: number) {
  return useQuery({
    queryKey: ['audits', id],
    queryFn: () => getAudit(id),
  });
}
