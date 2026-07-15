import { Chip } from '@mui/material';
import { statusColors } from '../theme';
import type { VulnerabilityStatus } from '../api/types/vulnerability';

export function StatusChip({ status }: { status: VulnerabilityStatus }) {
  return (
    <Chip
      label={status}
      size="small"
      variant="outlined"
      sx={{ borderColor: statusColors[status], color: statusColors[status], fontWeight: 600 }}
    />
  );
}
