import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createAudit } from '../api/endpoints/audits';

export function useCreateAudit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createAudit,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audits'] });
    },
  });
}
