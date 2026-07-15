import { useQuery } from '@tanstack/react-query';
import { getFrameworkSummary } from '../api/endpoints/frameworks';

export function useFrameworkSummary(shortName: string) {
  return useQuery({
    queryKey: ['frameworks', shortName, 'summary'],
    queryFn: () => getFrameworkSummary(shortName),
  });
}
