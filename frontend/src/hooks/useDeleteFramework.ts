import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deleteFramework } from '../api/endpoints/frameworks';

export function useDeleteFramework() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteFramework,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['frameworks'] });
    },
  });
}
