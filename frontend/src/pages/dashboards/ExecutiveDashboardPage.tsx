import { Box, Grid2 as Grid, Paper, Typography } from '@mui/material';
import { useExecutiveDashboard } from '../../hooks/useExecutiveDashboard';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { severityColors } from '../../theme';

function StatCard({ label, value }: { label: string; value: number | string }) {
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

export function ExecutiveDashboardPage() {
  const { data, isLoading, error } = useExecutiveDashboard();

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  if (!data) return null;

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Executive Dashboard
      </Typography>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid size={{ xs: 6, sm: 4 }}>
          <StatCard label="Total Assets" value={data.assets.total} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4 }}>
          <StatCard label="Total Vulnerabilities" value={data.vulnerabilities.total} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4 }}>
          <StatCard label="Total Controls" value={data.controls.total} />
        </Grid>
      </Grid>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <SeverityCard label="Critical" value={data.vulnerabilities.critical} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <SeverityCard label="High" value={data.vulnerabilities.high} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <SeverityCard label="Medium" value={data.vulnerabilities.medium} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <SeverityCard label="Low" value={data.vulnerabilities.low} />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Highest-Risk Asset
            </Typography>
            {data.assets.highest_risk_asset ? (
              <>
                <Typography variant="body1">{data.assets.highest_risk_asset.asset}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Risk score {data.assets.highest_risk_asset.risk_score} ·{' '}
                  {data.assets.highest_risk_asset.total_vulnerabilities} vulnerabilities
                </Typography>
              </>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No assets yet.
              </Typography>
            )}
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Top Risky Control (NIST CSF)
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Overall control risk score: {data.risk.overall_control_risk_score}
            </Typography>
            {data.risk.top_risky_control ? (
              <>
                <Typography variant="body1">
                  {data.risk.top_risky_control.control_id} — {data.risk.top_risky_control.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Risk score {data.risk.top_risky_control.risk_score} ·{' '}
                  {data.risk.top_risky_control.affected_vulnerabilities} affected vulnerabilities
                </Typography>
              </>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No mapped controls yet.
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
