import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Alert, Box, Card, CardContent, Divider, Grid2 as Grid, Typography } from '@mui/material';
import { useRisk } from '../../hooks/useRisk';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { SeverityChip } from '../../components/SeverityChip';
import { StatusChip } from '../../components/StatusChip';

function formatDateTime(value: string | null): string {
  return value ? new Date(value).toLocaleString() : '—';
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <Grid size={{ xs: 6, sm: 4 }}>
      <Typography variant="caption" color="text.secondary" display="block">
        {label}
      </Typography>
      <Typography variant="body2">{value ?? '—'}</Typography>
    </Grid>
  );
}

export function RiskDetailPage() {
  const { id } = useParams<{ id: string }>();
  const riskId = Number(id);

  const { data: risk, isLoading, error } = useRisk(riskId);

  if (isLoading) return <LoadingState />;

  if (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return (
        <Box sx={{ p: 3 }}>
          <Alert severity="warning">Risk not found.</Alert>
        </Box>
      );
    }
    return <ErrorState error={error} />;
  }

  if (!risk) return null;

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {risk.title}
      </Typography>

      <Card>
        <CardContent>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid size={{ xs: 6, sm: 4 }}>
              <Typography variant="caption" color="text.secondary" display="block">
                Level
              </Typography>
              {risk.risk_level ? <SeverityChip severity={risk.risk_level} /> : '—'}
            </Grid>
            <Grid size={{ xs: 6, sm: 4 }}>
              <Typography variant="caption" color="text.secondary" display="block">
                Status
              </Typography>
              <StatusChip status={risk.status} />
            </Grid>
            <Field label="Score" value={risk.risk_score} />
            <Field label="Impact" value={risk.impact} />
            <Field label="Likelihood" value={risk.likelihood} />
            <Field label="Owner" value={risk.owner} />
            <Field label="Source" value={risk.source} />
            <Field label="Due Date" value={formatDateTime(risk.due_date)} />
            <Field label="Created" value={formatDateTime(risk.created_at)} />
            <Field label="Updated" value={formatDateTime(risk.updated_at)} />
          </Grid>

          <Divider sx={{ my: 2 }} />

          <Typography variant="subtitle2" gutterBottom>
            Description
          </Typography>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
            {risk.description || '—'}
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
