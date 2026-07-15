import { useQuery } from '@tanstack/react-query';
import { getFrameworkGaps } from '../api/endpoints/frameworks';

export function useFrameworkGaps(shortName: string) {
  return useQuery({
    queryKey: ['frameworks', shortName, 'gaps'],
    queryFn: () => getFrameworkGaps(shortName),
  });
}
