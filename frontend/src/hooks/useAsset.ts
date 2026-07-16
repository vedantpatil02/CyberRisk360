import { useQuery } from '@tanstack/react-query';
import { getAsset } from '../api/endpoints/assets';

export function useAsset(id: number) {
  return useQuery({
    queryKey: ['assets', id],
    queryFn: () => getAsset(id),
  });
}
