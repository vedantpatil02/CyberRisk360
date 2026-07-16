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
import { useTechnicalReport } from '../../hooks/useTechnicalReport';
import { downloadReportPdf } from '../../api/endpoints/reports';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { SeverityChip } from '../../components/SeverityChip';
import { StatusChip } from '../../components/StatusChip';
import type { Finding } from '../../api/types/report';

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

function capitalize(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function FindingsTable({ severity, findings }: { severity: string; findings: Finding[] }) {
  return (
    <Box sx={{ mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <SeverityChip severity={capitalize(severity)} />
        <Typography variant="h6">({findings.length})</Typography>
      </Box>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>CVE</TableCell>
              <TableCell align="right">CVSS</TableCell>
              <TableCell>Asset</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Owner</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {findings.map((finding) => (
              <TableRow key={finding.id}>
                <TableCell>{finding.title}</TableCell>
                <TableCell>{finding.cve_id ?? '—'}</TableCell>
                <TableCell align="right">{finding.cvss_score ?? '—'}</TableCell>
                <TableCell>{finding.asset ?? '—'}</TableCell>
                <TableCell>
                  <StatusChip status={finding.status} />
                </TableCell>
                <TableCell>{finding.owner ?? '—'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

export function TechnicalReportPage() {
  const { data: report, isLoading, error } = useTechnicalReport();
  const [downloading, setDownloading] = useState(false);

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  if (!report) return null;

  const { sections } = report;

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await downloadReportPdf('/reports/technical', 'technical_vulnerability_report.pdf');
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
          <StatCard label="Total Findings" value={sections.summary.total_findings} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Affected Assets" value={sections.summary.affected_assets} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Open" value={sections.summary.by_status.open} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Closed" value={sections.summary.by_status.closed} />
        </Grid>
      </Grid>

      {sections.findings_by_severity.length === 0 && (
        <Typography color="text.secondary">No findings.</Typography>
      )}
      {sections.findings_by_severity.map((group) => (
        <FindingsTable key={group.severity} severity={group.severity} findings={group.findings} />
      ))}
    </Box>
  );
}
