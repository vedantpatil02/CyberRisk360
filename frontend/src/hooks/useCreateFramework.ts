import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createFramework } from '../api/endpoints/frameworks';

export function useCreateFramework() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createFramework,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['frameworks'] });
    },
  });
}
