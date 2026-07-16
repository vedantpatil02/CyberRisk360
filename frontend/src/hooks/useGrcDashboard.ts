import { useQuery } from '@tanstack/react-query';
import { getGrcDashboard } from '../api/endpoints/dashboard';

export function useGrcDashboard(frameworkName: string) {
  return useQuery({
    queryKey: ['dashboard', 'grc', frameworkName],
    queryFn: () => getGrcDashboard(frameworkName),
  });
}
