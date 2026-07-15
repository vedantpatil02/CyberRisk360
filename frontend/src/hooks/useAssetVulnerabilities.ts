import { useQuery } from '@tanstack/react-query';
import { getAssetVulnerabilities } from '../api/endpoints/assets';

export function useAssetVulnerabilities(id: number) {
  return useQuery({
    queryKey: ['assets', id, 'vulnerabilities'],
    queryFn: () => getAssetVulnerabilities(id),
  });
}
