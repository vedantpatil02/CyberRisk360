import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#1565c0' },
  },
});

// Single source of truth for severity/status color tokens, reused by
// SeverityChip/StatusChip so every page renders these consistently.
export const severityColors: Record<string, string> = {
  Critical: '#b71c1c',
  High: '#e65100',
  Medium: '#f9a825',
  Low: '#2e7d32',
};

// Covers both VulnerabilityStatus (Open/Closed) and RiskStatus (which
// adds Under Review/Mitigated/Accepted) - shared so both domains
// render consistently.
export const statusColors: Record<string, string> = {
  Open: '#c62828',
  'Under Review': '#f9a825',
  Mitigated: '#2e7d32',
  Accepted: '#1565c0',
  Closed: '#616161',
};
