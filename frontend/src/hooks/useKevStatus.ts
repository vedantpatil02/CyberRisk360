import { useQuery } from '@tanstack/react-query';
import { getKevStatus } from '../api/endpoints/vulnerabilities';

export function useKevStatus(id: number, hasCveId: boolean) {
  return useQuery({
    queryKey: ['vulnerabilities', id, 'kev-status'],
    queryFn: () => getKevStatus(id),
    // Skip the request entirely when there's no cve_id to check -
    // matches the backend's own short-circuit in check_kev_status.
    enabled: hasCveId,
  });
}
