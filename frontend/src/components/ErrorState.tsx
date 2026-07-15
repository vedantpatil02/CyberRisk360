import { Alert, AlertTitle } from '@mui/material';
import axios from 'axios';

function extractMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
    if (error.message) return error.message;
  }
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred.';
}

export function ErrorState({ error }: { error: unknown }) {
  return (
    <Alert severity="error">
      <AlertTitle>Something went wrong</AlertTitle>
      {extractMessage(error)}
    </Alert>
  );
}
