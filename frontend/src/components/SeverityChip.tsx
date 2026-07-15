import { Chip } from '@mui/material';
import { severityColors } from '../theme';
import type { Severity } from '../api/types/vulnerability';

export function SeverityChip({ severity }: { severity: Severity }) {
  return (
    <Chip
      label={severity}
      size="small"
      sx={{
        backgroundColor: severityColors[severity],
        color: '#fff',
        fontWeight: 600,
      }}
    />
  );
}
