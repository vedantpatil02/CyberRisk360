import { useQuery } from '@tanstack/react-query';
import { getExecutiveDashboard } from '../api/endpoints/dashboard';

export function useExecutiveDashboard() {
  return useQuery({
    queryKey: ['dashboard', 'executive'],
    queryFn: getExecutiveDashboard,
  });
}
