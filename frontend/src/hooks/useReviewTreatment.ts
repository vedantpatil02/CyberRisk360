import { useMutation, useQueryClient } from '@tanstack/react-query';
import { approveTreatment, rejectTreatment } from '../api/endpoints/risks';

export function useReviewTreatment(riskId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ approve, note }: { approve: boolean; note?: string }) =>
      approve ? approveTreatment(riskId, note) : rejectTreatment(riskId, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risks'] });
    },
  });
}
