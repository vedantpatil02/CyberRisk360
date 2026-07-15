import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { listVulnerabilities } from '../api/endpoints/vulnerabilities';
import type { VulnerabilityListParams } from '../api/types/vulnerability';

export function useVulnerabilities(params: VulnerabilityListParams) {
  return useQuery({
    queryKey: ['vulnerabilities', params],
    queryFn: () => listVulnerabilities(params),
    // Keeps the current page's rows visible while the next page/sort/
    // filter combination loads, instead of flashing a spinner over
    // existing rows on every interaction.
    placeholderData: keepPreviousData,
  });
}
