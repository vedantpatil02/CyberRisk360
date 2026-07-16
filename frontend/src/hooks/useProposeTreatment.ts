import { useMutation, useQueryClient } from '@tanstack/react-query';
import { proposeTreatment } from '../api/endpoints/risks';
import type { TreatmentType } from '../api/types/risk';

export function useProposeTreatment(riskId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: { treatment_type: TreatmentType; justification: string }) =>
      proposeTreatment(riskId, body),
    // Invalidating the 'risks' prefix covers the detail (['risks', id]),
    // every list-page variant (['risks', params]), and the treatment
    // history (['risks', id, 'treatment', 'history']) in one call.
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risks'] });
    },
  });
}
