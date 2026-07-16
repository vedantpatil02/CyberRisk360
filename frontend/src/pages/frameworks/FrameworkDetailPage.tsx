import { useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Grid2 as Grid,
  MenuItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import axios from 'axios';
import { useFrameworkSummary } from '../../hooks/useFrameworkSummary';
import { useFrameworkGaps } from '../../hooks/useFrameworkGaps';
import { useSubmitControlReview } from '../../hooks/useSubmitControlReview';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { StatusChip } from '../../components/StatusChip';
import { useAuth } from '../../auth/AuthContext';
import { hasRole } from '../../api/types/auth';
import { CONTROL_REVIEW_ROLES } from '../../api/endpoints/controls';
import type { FrameworkGapControl } from '../../api/types/framework';

const STATUS_OPTIONS = ['Missing', 'Partially Implemented', 'Implemented'];

function mutationErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
  }
  return 'Something went wrong.';
}

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

function ReviewControlForm({ controlId, onDone }: { controlId: number; onDone: () => void }) {
  const [newStatus, setNewStatus] = useState('Implemented');
  const [notes, setNotes] = useState('');
  const mutation = useSubmitControlReview(controlId);

  return (
    <TableRow>
      <TableCell colSpan={4}>
        <Box
          component="form"
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate({ new_status: newStatus, notes: notes || undefined }, { onSuccess: onDone });
          }}
          sx={{ display: 'flex', gap: 2, alignItems: 'flex-start', flexWrap: 'wrap', py: 1 }}
        >
          <TextField
            select
            label="New Status"
            size="small"
            value={newStatus}
            onChange={(e) => setNewStatus(e.target.value)}
            sx={{ minWidth: 180 }}
          >
            {STATUS_OPTIONS.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="Notes"
            size="small"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            sx={{ flex: 1, minWidth: 240 }}
          />
          <Button type="submit" variant="contained" size="small" disabled={mutation.isPending}>
            Submit Review
          </Button>
          <Button size="small" onClick={onDone}>
            Cancel
          </Button>
          {mutation.isError && (
            <Alert severity="error" sx={{ width: '100%' }}>
              {mutationErrorMessage(mutation.error)}
            </Alert>
          )}
        </Box>
      </TableCell>
    </TableRow>
  );
}

function ControlsTable({ title, controls }: { title: string; controls: FrameworkGapControl[] }) {
  const { user } = useAuth();
  const [reviewingId, setReviewingId] = useState<number | null>(null);
  const canReview = user !== null && hasRole(user.role, CONTROL_REVIEW_ROLES);

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
              <TableCell>Status</TableCell>
              <TableCell align="right">Approved Mappings</TableCell>
              {canReview && <TableCell align="right">Actions</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {controls.length === 0 && (
              <TableRow>
                <TableCell colSpan={canReview ? 5 : 4}>None.</TableCell>
              </TableRow>
            )}
            {controls.map((control) =>
              reviewingId === control.id ? (
                <ReviewControlForm
                  key={control.control_id}
                  controlId={control.id}
                  onDone={() => setReviewingId(null)}
                />
              ) : (
                <TableRow key={control.control_id}>
                  <TableCell>{control.control_id}</TableCell>
                  <TableCell>{control.name}</TableCell>
                  <TableCell>
                    <StatusChip status={control.status} />
                  </TableCell>
                  <TableCell align="right">{control.affected_vulnerabilities}</TableCell>
                  {canReview && (
                    <TableCell align="right">
                      <Button size="small" onClick={() => setReviewingId(control.id)}>
                        Review
                      </Button>
                    </TableCell>
                  )}
                </TableRow>
              ),
            )}
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
