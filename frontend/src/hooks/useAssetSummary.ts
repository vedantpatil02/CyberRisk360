import { useQuery } from '@tanstack/react-query';
import { getAssetSummary } from '../api/endpoints/assets';

export function useAssetSummary(id: number) {
  return useQuery({
    queryKey: ['assets', id, 'summary'],
    queryFn: () => getAssetSummary(id),
  });
}
