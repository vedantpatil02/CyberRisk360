import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  deleteEvidence,
  listRiskEvidence,
  listVulnerabilityEvidence,
  uploadRiskEvidence,
  uploadVulnerabilityEvidence,
} from '../api/endpoints/evidence';

type Resource = 'vulnerabilities' | 'risks';

export function useEvidence(resource: Resource, id: number) {
  return useQuery({
    queryKey: [resource, id, 'evidence'],
    queryFn: () =>
      resource === 'vulnerabilities' ? listVulnerabilityEvidence(id) : listRiskEvidence(id),
  });
}

export function useUploadEvidence(resource: Resource, id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, expiresAt }: { file: File; expiresAt: string | null }) =>
      resource === 'vulnerabilities'
        ? uploadVulnerabilityEvidence(id, file, expiresAt)
        : uploadRiskEvidence(id, file, expiresAt),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [resource, id, 'evidence'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}

export function useDeleteEvidence(resource: Resource, id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (attachmentId: number) => deleteEvidence(attachmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [resource, id, 'evidence'] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}
