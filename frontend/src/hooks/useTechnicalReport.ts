import { useQuery } from '@tanstack/react-query';
import { getTechnicalReport } from '../api/endpoints/reports';

export function useTechnicalReport() {
  return useQuery({
    queryKey: ['reports', 'technical'],
    queryFn: getTechnicalReport,
  });
}
