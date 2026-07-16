import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateAsset } from '../api/endpoints/assets';
import type { AssetUpdateInput } from '../api/types/asset';

export function useUpdateAsset(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: AssetUpdateInput) => updateAsset(id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    },
  });
}
