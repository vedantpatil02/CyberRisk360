import { useQuery } from '@tanstack/react-query';
import { getTreatmentHistory } from '../api/endpoints/risks';

export function useRiskTreatmentHistory(id: number) {
  return useQuery({
    queryKey: ['risks', id, 'treatment', 'history'],
    queryFn: () => getTreatmentHistory(id),
  });
}
