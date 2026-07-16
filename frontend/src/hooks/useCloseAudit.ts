import { useMutation, useQueryClient } from '@tanstack/react-query';
import { closeAudit } from '../api/endpoints/audits';

export function useCloseAudit(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => closeAudit(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audits'] });
    },
  });
}
