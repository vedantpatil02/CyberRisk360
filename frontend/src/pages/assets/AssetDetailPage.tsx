import { useParams } from 'react-router-dom';
import axios from 'axios';
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
import { useAssetSummary } from '../../hooks/useAssetSummary';
import { useAssetVulnerabilities } from '../../hooks/useAssetVulnerabilities';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { severityColors } from '../../theme';

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <Paper sx={{ p: 2, textAlign: 'center', borderTop: 4, borderColor: severityColors[label] }}>
      <Typography variant="h5">{value}</Typography>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
    </Paper>
  );
}

export function AssetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const assetId = Number(id);

  const { data: summary, isLoading, error } = useAssetSummary(assetId);
  const { data: vulnerabilities, isLoading: vulnsLoading } = useAssetVulnerabilities(assetId);

  if (isLoading) return <LoadingState />;

  if (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return (
        <Box sx={{ p: 3 }}>
          <Alert severity="warning">Asset not found.</Alert>
        </Box>
      );
    }
    return <ErrorState error={error} />;
  }

  if (!summary) return null;

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {summary.asset_name}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Asset ID: {summary.asset_id} — full asset fields (owner, criticality, IP, environment)
        aren&apos;t available from a single-asset lookup yet; see the Assets list.
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Critical" value={summary.critical} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="High" value={summary.high} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Medium" value={summary.medium} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Low" value={summary.low} />
        </Grid>
      </Grid>

      <Typography variant="h6" gutterBottom>
        Vulnerabilities ({summary.total})
      </Typography>
      {vulnsLoading ? (
        <LoadingState />
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Title</TableCell>
                <TableCell>Severity</TableCell>
                <TableCell align="right">CVSS</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(!vulnerabilities || vulnerabilities.length === 0) && (
                <TableRow>
                  <TableCell colSpan={4}>No vulnerabilities on this asset.</TableCell>
                </TableRow>
              )}
              {vulnerabilities?.map((vuln) => (
                <TableRow key={vuln.id}>
                  <TableCell>{vuln.title}</TableCell>
                  <TableCell>{vuln.severity}</TableCell>
                  <TableCell align="right">{vuln.cvss_score}</TableCell>
                  <TableCell>{vuln.status}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}
