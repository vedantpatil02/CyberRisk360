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

// Covers VulnerabilityStatus (Open/Closed), RiskStatus (which adds
// Under Review/Mitigated/Accepted/Transferred/Avoided),
// AuditStatus (Planned/In Progress/Completed), AuditFindingStatus
// (which adds Remediated), and Control.status (Missing/Partially
// Implemented/Implemented) - shared so every domain renders
// consistently.
export const statusColors: Record<string, string> = {
  Open: '#c62828',
  'Under Review': '#f9a825',
  Mitigated: '#2e7d32',
  Accepted: '#1565c0',
  Transferred: '#6a1b9a',
  Avoided: '#00838f',
  Planned: '#546e7a',
  'In Progress': '#f9a825',
  Completed: '#2e7d32',
  Remediated: '#2e7d32',
  Missing: '#c62828',
  'Partially Implemented': '#f9a825',
  Implemented: '#2e7d32',
  Closed: '#616161',
};
