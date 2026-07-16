import { useState } from 'react';
import { useParams } from 'react-router-dom';
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
import { useComplianceReport } from '../../hooks/useComplianceReport';
import { downloadReportPdf } from '../../api/endpoints/reports';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import type { ControlRiskRow } from '../../api/types/report';
import type { FrameworkGapControl } from '../../api/types/framework';

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

// Same shape/idiom as FrameworkDetailPage's ControlsTable - the
// compliance report's gaps section returns identical
// {control_id, name, affected_vulnerabilities} rows.
function ControlsTable({ title, controls }: { title: string; controls: FrameworkGapControl[] }) {
  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        {title} ({controls.length})
      </Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Control ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell align="right">Approved Mappings</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {controls.length === 0 && (
              <TableRow>
                <TableCell colSpan={3}>None.</TableCell>
              </TableRow>
            )}
            {controls.map((control) => (
              <TableRow key={control.control_id}>
                <TableCell>{control.control_id}</TableCell>
                <TableCell>{control.name}</TableCell>
                <TableCell align="right">{control.affected_vulnerabilities}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

function ControlRiskTable({ controls }: { controls: ControlRiskRow[] }) {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Control Risk
      </Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Control ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell align="right">Affected Vulnerabilities</TableCell>
              <TableCell align="right">Risk Score</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {controls.length === 0 && (
              <TableRow>
                <TableCell colSpan={4}>No controls found.</TableCell>
              </TableRow>
            )}
            {controls.map((control) => (
              <TableRow key={control.control_id}>
                <TableCell>{control.control_id}</TableCell>
                <TableCell>{control.name}</TableCell>
                <TableCell align="right">{control.affected_vulnerabilities}</TableCell>
                <TableCell align="right">{control.risk_score}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

export function ComplianceReportPage() {
  const { shortName } = useParams<{ shortName: string }>();
  const name = shortName ?? '';

  const { data: report, isLoading, error } = useComplianceReport(name);
  const [downloading, setDownloading] = useState(false);

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  if (!report) return null;

  const { sections } = report;

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await downloadReportPdf(
        `/reports/compliance/${name}`,
        `compliance_assessment_${name}.pdf`,
      );
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
            {sections.framework.version} · Generated{' '}
            {new Date(report.generated_at).toLocaleString()} by {report.generated_by}
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
          <StatCard label="Total Controls" value={sections.compliance_summary.total_controls} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Implemented" value={sections.compliance_summary.implemented} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Partial" value={sections.compliance_summary.partial} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Missing" value={sections.compliance_summary.missing} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard
            label="Compliance Score"
            value={`${sections.compliance_summary.compliance_score}%`}
          />
        </Grid>
      </Grid>

      <ControlsTable title="Controls with coverage" controls={sections.gaps.affected_controls} />
      <ControlsTable
        title="Controls without coverage"
        controls={sections.gaps.unaffected_controls}
      />
      <ControlRiskTable controls={sections.control_risk} />
    </Box>
  );
}
