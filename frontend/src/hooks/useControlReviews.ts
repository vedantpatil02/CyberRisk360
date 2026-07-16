import { useQuery } from '@tanstack/react-query';
import { getControlReviews } from '../api/endpoints/controls';

export function useControlReviews(controlId: number) {
  return useQuery({
    queryKey: ['controls', controlId, 'reviews'],
    queryFn: () => getControlReviews(controlId),
  });
}
