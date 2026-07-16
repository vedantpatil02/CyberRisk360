import { useQuery } from '@tanstack/react-query';
import { getComplianceReport } from '../api/endpoints/reports';

export function useComplianceReport(shortName: string) {
  return useQuery({
    queryKey: ['reports', 'compliance', shortName],
    queryFn: () => getComplianceReport(shortName),
  });
}
