import { useQuery } from '@tanstack/react-query';
import { getEpssScore } from '../api/endpoints/vulnerabilities';

export function useEpssScore(id: number, hasCveId: boolean) {
  return useQuery({
    queryKey: ['vulnerabilities', id, 'epss-score'],
    queryFn: () => getEpssScore(id),
    // Skip the request entirely when there's no cve_id to check -
    // matches the backend's own short-circuit in get_epss_score.
    enabled: hasCveId,
  });
}
