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
import { useGrcDashboard } from '../../hooks/useGrcDashboard';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';

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

export function GrcDashboardPage() {
  const { shortName } = useParams<{ shortName: string }>();
  const name = shortName ?? '';

  const { data, isLoading, error } = useGrcDashboard(name);

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  if (!data) return null;

  // GET /dashboard/grc/{framework} never 404s for an unknown framework
  // (it just returns zeros across the board) - same inference
  // FrameworkDetailPage already uses for "not found".
  if (data.total_controls === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning">Framework not found.</Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        GRC Dashboard — {data.framework}
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Compliance Score" value={`${data.compliance_score}%`} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Implemented" value={data.implemented_controls} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Partial" value={data.partial_controls} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Missing" value={data.missing_controls} />
        </Grid>
      </Grid>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, sm: 4 }}>
          <StatCard label="Overall Risk Score" value={data.overall_risk_score} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4 }}>
          <StatCard label="Controls with Gaps" value={data.gap_summary.affected_controls} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4 }}>
          <StatCard label="Controls without Gaps" value={data.gap_summary.unaffected_controls} />
        </Grid>
      </Grid>

      <Typography variant="h6" gutterBottom>
        Top Risky Controls
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
            {data.top_risky_controls.length === 0 && (
              <TableRow>
                <TableCell colSpan={4}>No risk-mapped controls yet.</TableCell>
              </TableRow>
            )}
            {data.top_risky_controls.map((control) => (
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
