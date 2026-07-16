import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { approveMapping, listPendingMappings, rejectMapping } from '../api/endpoints/mappings';

export function usePendingMappings() {
  return useQuery({
    queryKey: ['mappings', 'pending'],
    queryFn: listPendingMappings,
  });
}

export function useReviewMapping() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, approve, note }: { id: number; approve: boolean; note?: string }) =>
      approve ? approveMapping(id, note) : rejectMapping(id, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mappings'] });
    },
  });
}
