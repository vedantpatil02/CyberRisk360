import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateRisk } from '../api/endpoints/risks';
import type { RiskUpdateInput } from '../api/types/risk';

export function useUpdateRisk(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: RiskUpdateInput) => updateRisk(id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risks'] });
    },
  });
}
