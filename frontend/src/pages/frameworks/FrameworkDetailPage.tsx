import { useParams } from 'react-router-dom';
import {
  Alert,
  Box,
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
import { useFrameworkSummary } from '../../hooks/useFrameworkSummary';
import { useFrameworkGaps } from '../../hooks/useFrameworkGaps';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
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

export function FrameworkDetailPage() {
  const { shortName } = useParams<{ shortName: string }>();
  const name = shortName ?? '';

  const {
    data: summary,
    isLoading: summaryLoading,
    error: summaryError,
  } = useFrameworkSummary(name);
  const { data: gaps, isLoading: gapsLoading, error: gapsError } = useFrameworkGaps(name);

  if (summaryLoading || gapsLoading) return <LoadingState />;
  if (summaryError) return <ErrorState error={summaryError} />;
  if (gapsError) return <ErrorState error={gapsError} />;
  if (!summary || !gaps) return null;

  // Neither endpoint 404s for an unknown short_name (both just query
  // for zero matching controls) - an empty result is the only signal
  // available to distinguish "unknown framework" from "framework with
  // no controls yet".
  if (summary.total_controls === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning">
          Framework &quot;{name}&quot; not found, or has no controls.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {name}
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Total Controls" value={summary.total_controls} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Controls with Coverage" value={summary.affected_controls} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Approved Mappings" value={summary.affected_vulnerabilities} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard
            label="Vulnerability Coverage Score"
            value={`${summary.vulnerability_coverage_score}%`}
          />
        </Grid>
      </Grid>

      <ControlsTable title="Controls with coverage" controls={gaps.affected_controls} />
      <ControlsTable title="Controls without coverage" controls={gaps.unaffected_controls} />
    </Box>
  );
}
