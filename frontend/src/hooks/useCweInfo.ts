import { useQuery } from '@tanstack/react-query';
import { getCweInfo } from '../api/endpoints/vulnerabilities';

// Unlike useKevStatus/useEpssScore, no `enabled` gate on cve_id - the
// backend resolves a CWE from title/description regex extraction too,
// so it's worth calling even without one (matches the endpoint's own
// resolution order).
export function useCweInfo(id: number) {
  return useQuery({
    queryKey: ['vulnerabilities', id, 'cwe-info'],
    queryFn: () => getCweInfo(id),
  });
}
