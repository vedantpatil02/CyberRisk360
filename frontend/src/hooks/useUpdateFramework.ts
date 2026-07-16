import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateFramework } from '../api/endpoints/frameworks';
import type { FrameworkUpdateInput } from '../api/types/framework';

export function useUpdateFramework(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: FrameworkUpdateInput) => updateFramework(id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['frameworks'] });
    },
  });
}
