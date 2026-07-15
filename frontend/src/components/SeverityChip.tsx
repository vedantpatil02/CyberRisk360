import { Chip } from '@mui/material';
import { severityColors } from '../theme';

// Shared by Vulnerabilities (severity) and Risks (risk_level) - both
// use the identical Critical/High/Medium/Low strings, so one
// component covers both rather than duplicating chip markup.
export function SeverityChip({ severity }: { severity: string }) {
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
