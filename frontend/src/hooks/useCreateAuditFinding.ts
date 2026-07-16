import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createAuditFinding } from '../api/endpoints/audits';
import type { AuditFindingCreateInput } from '../api/types/audit';

export function useCreateAuditFinding(auditId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: AuditFindingCreateInput) => createAuditFinding(auditId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audits', auditId, 'findings'] });
    },
  });
}
