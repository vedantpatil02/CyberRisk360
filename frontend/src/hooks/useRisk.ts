import { useQuery } from '@tanstack/react-query';
import { getRisk } from '../api/endpoints/risks';

export function useRisk(id: number) {
  return useQuery({
    queryKey: ['risks', id],
    queryFn: () => getRisk(id),
  });
}
