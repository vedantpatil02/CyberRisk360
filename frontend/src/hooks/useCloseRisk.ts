import { useMutation, useQueryClient } from '@tanstack/react-query';
import { closeRisk } from '../api/endpoints/risks';

export function useCloseRisk(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => closeRisk(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risks'] });
    },
  });
}
