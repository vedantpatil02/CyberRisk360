import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadReport } from '../api/endpoints/imports';

export function useUploadReport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => uploadReport(file),
    onSuccess: () => {
      // A successful import writes new vulnerabilities (and possibly
      // assets) - invalidate every list/dashboard that summarizes them.
      queryClient.invalidateQueries({ queryKey: ['vulnerabilities'] });
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}
