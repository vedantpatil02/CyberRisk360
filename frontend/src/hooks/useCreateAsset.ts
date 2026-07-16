import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createAsset } from '../api/endpoints/assets';

export function useCreateAsset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createAsset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    },
  });
}
