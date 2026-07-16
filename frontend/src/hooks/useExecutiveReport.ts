import { useQuery } from '@tanstack/react-query';
import { getExecutiveReport } from '../api/endpoints/reports';

export function useExecutiveReport() {
  return useQuery({
    queryKey: ['reports', 'executive'],
    queryFn: getExecutiveReport,
  });
}
