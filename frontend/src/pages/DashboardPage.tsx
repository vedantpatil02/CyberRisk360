import {
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
import { useDashboardOverview } from '../hooks/useDashboardOverview';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { severityColors } from '../theme';

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <Paper sx={{ p: 2, textAlign: 'center' }}>
      <Typography variant="h4">{value}</Typography>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
    </Paper>
  );
}

function SeverityCard({ label, value }: { label: string; value: number }) {
  return (
    <Paper sx={{ p: 2, textAlign: 'center', borderTop: 4, borderColor: severityColors[label] }}>
      <Typography variant="h4">{value}</Typography>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
    </Paper>
  );
}

export function DashboardPage() {
  const { data, isLoading, error } = useDashboardOverview();

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  if (!data) return null;

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Overview
      </Typography>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Total Assets" value={data.total_assets} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Total Vulnerabilities" value={data.total_vulnerabilities} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Open" value={data.open} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Closed" value={data.closed} />
        </Grid>
      </Grid>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <SeverityCard label="Critical" value={data.critical} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <SeverityCard label="High" value={data.high} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <SeverityCard label="Medium" value={data.medium} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <SeverityCard label="Low" value={data.low} />
        </Grid>
      </Grid>

      <Typography variant="h6" gutterBottom>
        Top Assets by Vulnerability Count
      </Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Asset</TableCell>
              <TableCell align="right">Vulnerabilities</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.top_assets.length === 0 && (
              <TableRow>
                <TableCell colSpan={2}>No assets yet.</TableCell>
              </TableRow>
            )}
            {data.top_assets.map((asset) => (
              <TableRow key={asset.asset_id}>
                <TableCell>{asset.asset_name}</TableCell>
                <TableCell align="right">{asset.vulnerability_count}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
