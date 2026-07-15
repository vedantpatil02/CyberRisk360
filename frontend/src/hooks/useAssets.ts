import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { listAssets } from '../api/endpoints/assets';
import type { AssetListParams } from '../api/types/asset';

export function useAssets(params: AssetListParams) {
  return useQuery({
    queryKey: ['assets', params],
    queryFn: () => listAssets(params),
    placeholderData: keepPreviousData,
  });
}
