import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createOrganization, listOrganizations } from '../api/endpoints/organizations';
import type { OrganizationCreateInput } from '../api/types/organization';

export function useOrganizations() {
  return useQuery({
    queryKey: ['organizations'],
    queryFn: listOrganizations,
  });
}

export function useCreateOrganization() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: OrganizationCreateInput) => createOrganization(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organizations'] });
    },
  });
}
