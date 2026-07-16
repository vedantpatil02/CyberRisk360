import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createRisk } from '../api/endpoints/risks';

export function useCreateRisk() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createRisk,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risks'] });
    },
  });
}
