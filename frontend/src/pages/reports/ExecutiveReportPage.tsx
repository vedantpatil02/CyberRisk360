import { useState } from 'react';
import {
  Box,
  Button,
  Grid2 as Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import { useExecutiveReport } from '../../hooks/useExecutiveReport';
import { downloadReportPdf } from '../../api/endpoints/reports';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { SeverityChip } from '../../components/SeverityChip';
import { StatusChip } from '../../components/StatusChip';

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Paper sx={{ p: 2, textAlign: 'center' }}>
      <Typography variant="h5">{value}</Typography>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
    </Paper>
  );
}

// Breakdown dict keys (by_severity/by_status) are lowercase, but
// SeverityChip/StatusChip are colored off theme.ts maps keyed by the
// capitalized display strings used everywhere else in the app.
function capitalize(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function ExecutiveReportPage() {
  const { data: report, isLoading, error } = useExecutiveReport();
  const [downloading, setDownloading] = useState(false);

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  if (!report) return null;

  const { sections } = report;

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await downloadReportPdf('/reports/executive', 'executive_summary.pdf');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="h5">{report.title}</Typography>
          <Typography variant="body2" color="text.secondary">
            Generated {new Date(report.generated_at).toLocaleString()} by {report.generated_by}
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={handleDownload}
          disabled={downloading}
        >
          {downloading ? 'Preparing PDF…' : 'Download PDF'}
        </Button>
      </Box>

      <Grid container spacing={2} sx={{ mb: 3, mt: 1 }}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Total Assets" value={sections.overview.total_assets} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Total Vulnerabilities" value={sections.overview.total_vulnerabilities} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Total Controls" value={sections.overview.total_controls} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard
            label="Overall Control Risk Score"
            value={sections.overview.overall_control_risk_score}
          />
        </Grid>
      </Grid>

      <Box sx={{ display: 'flex', gap: 5, flexWrap: 'wrap', mb: 3 }}>
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Vulnerabilities by Severity
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            {(['critical', 'high', 'medium', 'low'] as const).map((key) => (
              <Box key={key} sx={{ textAlign: 'center' }}>
                <SeverityChip severity={capitalize(key)} />
                <Typography variant="body2">{sections.vulnerabilities.by_severity[key]}</Typography>
              </Box>
            ))}
          </Box>
        </Box>
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Vulnerabilities by Status
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            {(['open', 'closed'] as const).map((key) => (
              <Box key={key} sx={{ textAlign: 'center' }}>
                <StatusChip status={capitalize(key)} />
                <Typography variant="body2">{sections.vulnerabilities.by_status[key]}</Typography>
              </Box>
            ))}
          </Box>
        </Box>
      </Box>

      <Typography variant="h6" gutterBottom>
        Top Risk Assets
      </Typography>
      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Asset</TableCell>
              <TableCell align="right">Critical</TableCell>
              <TableCell align="right">High</TableCell>
              <TableCell align="right">Medium</TableCell>
              <TableCell align="right">Low</TableCell>
              <TableCell align="right">Risk Score</TableCell>
              <TableCell align="right">Total Vulnerabilities</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sections.top_risk_assets.length === 0 && (
              <TableRow>
                <TableCell colSpan={7}>No assets found.</TableCell>
              </TableRow>
            )}
            {sections.top_risk_assets.map((row, index) => (
              <TableRow key={`${row.asset}-${index}`}>
                <TableCell>{row.asset}</TableCell>
                <TableCell align="right">{row.critical}</TableCell>
                <TableCell align="right">{row.high}</TableCell>
                <TableCell align="right">{row.medium}</TableCell>
                <TableCell align="right">{row.low}</TableCell>
                <TableCell align="right">{row.risk_score}</TableCell>
                <TableCell align="right">{row.total_vulnerabilities}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Typography variant="h6" gutterBottom>
        Framework Compliance
      </Typography>
      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Framework</TableCell>
              <TableCell>Version</TableCell>
              <TableCell align="right">Total Controls</TableCell>
              <TableCell align="right">Implemented</TableCell>
              <TableCell align="right">Partial</TableCell>
              <TableCell align="right">Missing</TableCell>
              <TableCell align="right">Compliance Score</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sections.framework_compliance.length === 0 && (
              <TableRow>
                <TableCell colSpan={7}>No frameworks found.</TableCell>
              </TableRow>
            )}
            {sections.framework_compliance.map((row) => (
              <TableRow key={row.short_name}>
                <TableCell>{row.framework}</TableCell>
                <TableCell>{row.version}</TableCell>
                <TableCell align="right">{row.total_controls}</TableCell>
                <TableCell align="right">{row.implemented}</TableCell>
                <TableCell align="right">{row.partial}</TableCell>
                <TableCell align="right">{row.missing}</TableCell>
                <TableCell align="right">{row.compliance_score}%</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Typography variant="h6" gutterBottom>
        Top Risk Controls
      </Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Framework</TableCell>
              <TableCell>Control ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell align="right">Affected Vulnerabilities</TableCell>
              <TableCell align="right">Risk Score</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sections.top_risk_controls.length === 0 && (
              <TableRow>
                <TableCell colSpan={5}>No controls found.</TableCell>
              </TableRow>
            )}
            {sections.top_risk_controls.map((row, index) => (
              <TableRow key={`${row.framework}-${row.control_id}-${index}`}>
                <TableCell>{row.framework}</TableCell>
                <TableCell>{row.control_id}</TableCell>
                <TableCell>{row.name}</TableCell>
                <TableCell align="right">{row.affected_vulnerabilities}</TableCell>
                <TableCell align="right">{row.risk_score}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
