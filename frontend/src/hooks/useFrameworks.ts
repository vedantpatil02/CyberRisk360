import { useQuery } from '@tanstack/react-query';
import { listFrameworks } from '../api/endpoints/frameworks';

export function useFrameworks() {
  return useQuery({
    queryKey: ['frameworks'],
    queryFn: listFrameworks,
  });
}
