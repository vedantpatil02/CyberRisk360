import { useQuery } from '@tanstack/react-query';
import { getOverview } from '../api/endpoints/dashboard';

export function useDashboardOverview() {
  return useQuery({
    queryKey: ['dashboard', 'overview'],
    queryFn: getOverview,
  });
}
