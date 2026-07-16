import { useMutation, useQueryClient } from '@tanstack/react-query';
import { submitControlReview } from '../api/endpoints/controls';
import type { ControlReviewCreateInput } from '../api/types/control_review';

export function useSubmitControlReview(controlId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: ControlReviewCreateInput) => submitControlReview(controlId, input),
    onSuccess: () => {
      // Invalidates the framework's gaps/summary (status + coverage
      // numbers) and this control's own review history in one call
      // each - two different query-key prefixes since 'frameworks'
      // doesn't nest under a single control.
      queryClient.invalidateQueries({ queryKey: ['frameworks'] });
      queryClient.invalidateQueries({ queryKey: ['controls', controlId, 'reviews'] });
    },
  });
}
