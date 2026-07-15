import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { listRisks } from '../api/endpoints/risks';
import type { RiskListParams } from '../api/types/risk';

export function useRisks(params: RiskListParams) {
  return useQuery({
    queryKey: ['risks', params],
    queryFn: () => listRisks(params),
    placeholderData: keepPreviousData,
  });
}
