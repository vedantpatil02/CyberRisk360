import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateAuditFinding } from '../api/endpoints/audits';
import type { AuditFindingUpdateInput } from '../api/types/audit';

export function useUpdateAuditFinding(auditId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ findingId, input }: { findingId: number; input: AuditFindingUpdateInput }) =>
      updateAuditFinding(findingId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audits', auditId, 'findings'] });
    },
  });
}
