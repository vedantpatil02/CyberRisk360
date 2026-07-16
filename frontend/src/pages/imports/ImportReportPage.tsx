import { useRef } from 'react';
import { Alert, Box, Button, Card, CardContent, Typography } from '@mui/material';
import axios from 'axios';
import { useUploadReport } from '../../hooks/useUploadReport';

function mutationErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
  }
  return 'Something went wrong.';
}

export function ImportReportPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mutation = useUploadReport();

  const handleUpload = () => {
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;
    mutation.mutate(file, {
      onSuccess: () => {
        if (fileInputRef.current) fileInputRef.current.value = '';
      },
    });
  };

  return (
    <Box sx={{ maxWidth: 640 }}>
      <Typography variant="h5" gutterBottom>
        Import Scan Report
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Upload a Nessus CSV, native .nessus XML, or PDF report. Findings are parsed, enriched
        (CVE/plugin lookups), deduplicated, and written as vulnerabilities.
      </Typography>

      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            <input ref={fileInputRef} type="file" accept=".csv,.nessus,.pdf" />
            <Button variant="contained" disabled={mutation.isPending} onClick={handleUpload}>
              {mutation.isPending ? 'Uploading…' : 'Upload'}
            </Button>
          </Box>

          {mutation.isError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {mutationErrorMessage(mutation.error)}
            </Alert>
          )}

          {mutation.isSuccess && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Parsed {mutation.data.findings_detected} finding
              {mutation.data.findings_detected === 1 ? '' : 's'} from a {mutation.data.file_type}{' '}
              report.
              {mutation.data.import_result && (
                <>
                  {' '}
                  Imported {mutation.data.import_result.created} new vulnerabilit
                  {mutation.data.import_result.created === 1 ? 'y' : 'ies'} (
                  {mutation.data.import_result.duplicates} duplicate
                  {mutation.data.import_result.duplicates === 1 ? '' : 's'} skipped).
                </>
              )}
            </Alert>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
