import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateAudit } from '../api/endpoints/audits';
import type { AuditUpdateInput } from '../api/types/audit';

export function useUpdateAudit(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: AuditUpdateInput) => updateAudit(id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audits'] });
    },
  });
}
