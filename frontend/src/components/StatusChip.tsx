import { Chip } from '@mui/material';
import { statusColors } from '../theme';

// Shared by Vulnerabilities (Open/Closed) and Risks (which add Under
// Review/Mitigated/Accepted) - both are real, typed string unions at
// their call sites, so a plain `string` prop here doesn't lose any
// safety, just lets one component serve both domains.
export function StatusChip({ status }: { status: string }) {
  return (
    <Chip
      label={status}
      size="small"
      variant="outlined"
      sx={{ borderColor: statusColors[status], color: statusColors[status], fontWeight: 600 }}
    />
  );
}
