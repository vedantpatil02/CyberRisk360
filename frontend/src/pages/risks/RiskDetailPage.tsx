import { useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Divider,
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
import { useRisk } from '../../hooks/useRisk';
import { useRiskTreatmentHistory } from '../../hooks/useRiskTreatmentHistory';
import { useProposeTreatment } from '../../hooks/useProposeTreatment';
import { useReviewTreatment } from '../../hooks/useReviewTreatment';
import { useUpdateRisk } from '../../hooks/useUpdateRisk';
import { useCloseRisk } from '../../hooks/useCloseRisk';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { SeverityChip } from '../../components/SeverityChip';
import { StatusChip } from '../../components/StatusChip';
import { EvidenceSection } from '../../components/EvidenceSection';
import { useAuth } from '../../auth/AuthContext';
import { hasRole } from '../../api/types/auth';
import {
  RISK_TREATMENT_APPROVE_ROLES,
  RISK_TREATMENT_PROPOSE_ROLES,
  RISK_WRITE_ROLES,
} from '../../api/endpoints/risks';
import type { Risk, RiskUpdateInput, TreatmentType } from '../../api/types/risk';

const TREATMENT_OPTIONS: { value: TreatmentType; label: string }[] = [
  { value: 'mitigate', label: 'Mitigate' },
  { value: 'accept', label: 'Accept' },
  { value: 'transfer', label: 'Transfer' },
  { value: 'avoid', label: 'Avoid' },
];

function formatDateTime(value: string | null): string {
  return value ? new Date(value).toLocaleString() : '—';
}

function mutationErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
  }
  return 'Something went wrong.';
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

function EditRiskForm({ risk, onDone }: { risk: Risk; onDone: () => void }) {
  const [form, setForm] = useState<RiskUpdateInput>({
    title: risk.title,
    description: risk.description,
    impact: risk.impact,
    likelihood: risk.likelihood,
    owner: risk.owner ?? '',
  });
  const mutation = useUpdateRisk(risk.id);

  return (
    <Box
      component="form"
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate(form, { onSuccess: onDone });
      }}
      sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}
    >
      <TextField
        label="Title"
        size="small"
        required
        value={form.title}
        onChange={(e) => setForm({ ...form, title: e.target.value })}
        sx={{ flex: 1, minWidth: 200 }}
      />
      <TextField
        label="Impact (1-5)"
        size="small"
        type="number"
        slotProps={{ htmlInput: { min: 1, max: 5 } }}
        value={form.impact}
        onChange={(e) => setForm({ ...form, impact: Number(e.target.value) })}
        sx={{ width: 140 }}
      />
      <TextField
        label="Likelihood (1-5)"
        size="small"
        type="number"
        slotProps={{ htmlInput: { min: 1, max: 5 } }}
        value={form.likelihood}
        onChange={(e) => setForm({ ...form, likelihood: Number(e.target.value) })}
        sx={{ width: 140 }}
      />
      <TextField
        label="Owner"
        size="small"
        value={form.owner}
        onChange={(e) => setForm({ ...form, owner: e.target.value })}
        sx={{ width: 200 }}
      />
      <TextField
        label="Description"
        size="small"
        multiline
        value={form.description}
        onChange={(e) => setForm({ ...form, description: e.target.value })}
        sx={{ flex: '1 1 100%' }}
      />
      <Button type="submit" variant="contained" disabled={mutation.isPending}>
        Save
      </Button>
      <Button onClick={onDone}>Cancel</Button>
      {mutation.isError && (
        <Alert severity="error" sx={{ width: '100%' }}>
          {mutationErrorMessage(mutation.error)}
        </Alert>
      )}
    </Box>
  );
}

function ProposeTreatmentForm({ riskId }: { riskId: number }) {
  const [treatmentType, setTreatmentType] = useState<TreatmentType>('mitigate');
  const [justification, setJustification] = useState('');
  const mutation = useProposeTreatment(riskId);

  return (
    <Box
      component="form"
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate({ treatment_type: treatmentType, justification });
      }}
      sx={{ display: 'flex', gap: 2, alignItems: 'flex-start', flexWrap: 'wrap' }}
    >
      <TextField
        select
        label="Treatment"
        size="small"
        value={treatmentType}
        onChange={(e) => setTreatmentType(e.target.value as TreatmentType)}
        sx={{ minWidth: 160 }}
      >
        {TREATMENT_OPTIONS.map((option) => (
          <MenuItem key={option.value} value={option.value}>
            {option.label}
          </MenuItem>
        ))}
      </TextField>
      <TextField
        label="Justification"
        size="small"
        required
        value={justification}
        onChange={(e) => setJustification(e.target.value)}
        sx={{ flex: 1, minWidth: 240 }}
      />
      <Button type="submit" variant="contained" disabled={mutation.isPending}>
        Propose Treatment
      </Button>
      {mutation.isError && (
        <Alert severity="error" sx={{ width: '100%' }}>
          {mutationErrorMessage(mutation.error)}
        </Alert>
      )}
    </Box>
  );
}

function ReviewTreatmentForm({ riskId }: { riskId: number }) {
  const [note, setNote] = useState('');
  const mutation = useReviewTreatment(riskId);

  return (
    <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start', flexWrap: 'wrap' }}>
      <TextField
        label="Note (optional)"
        size="small"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        sx={{ flex: 1, minWidth: 240 }}
      />
      <Button
        variant="contained"
        color="success"
        disabled={mutation.isPending}
        onClick={() => mutation.mutate({ approve: true, note: note || undefined })}
      >
        Approve
      </Button>
      <Button
        variant="outlined"
        color="error"
        disabled={mutation.isPending}
        onClick={() => mutation.mutate({ approve: false, note: note || undefined })}
      >
        Reject
      </Button>
      {mutation.isError && (
        <Alert severity="error" sx={{ width: '100%' }}>
          {mutationErrorMessage(mutation.error)}
        </Alert>
      )}
    </Box>
  );
}

function TreatmentHistory({ riskId }: { riskId: number }) {
  const { data, isLoading } = useRiskTreatmentHistory(riskId);

  if (isLoading) return null;
  if (!data || data.length === 0) return null;

  return (
    <TableContainer component={Paper} sx={{ mt: 2 }}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Action</TableCell>
            <TableCell>Treatment</TableCell>
            <TableCell>Status Change</TableCell>
            <TableCell>Actor</TableCell>
            <TableCell>Note</TableCell>
            <TableCell align="right">When</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((entry) => (
            <TableRow key={entry.id}>
              <TableCell sx={{ textTransform: 'capitalize' }}>{entry.action}</TableCell>
              <TableCell sx={{ textTransform: 'capitalize' }}>
                {entry.treatment_type ?? '—'}
              </TableCell>
              <TableCell>
                {entry.previous_status ?? '—'} → {entry.new_status}
              </TableCell>
              <TableCell>{entry.actor ?? '—'}</TableCell>
              <TableCell>{entry.note ?? '—'}</TableCell>
              <TableCell align="right">{formatDateTime(entry.created_at)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export function RiskDetailPage() {
  const { id } = useParams<{ id: string }>();
  const riskId = Number(id);
  const { user } = useAuth();
  const [editing, setEditing] = useState(false);

  const { data: risk, isLoading, error } = useRisk(riskId);
  const closeMutation = useCloseRisk(riskId);

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

  const canWrite = user !== null && hasRole(user.role, RISK_WRITE_ROLES);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" gutterBottom>
          {risk.title}
        </Typography>
        {canWrite && !editing && (
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button variant="outlined" onClick={() => setEditing(true)}>
              Edit
            </Button>
            {risk.status !== 'Closed' && (
              <Button
                variant="outlined"
                color="success"
                disabled={closeMutation.isPending}
                onClick={() => closeMutation.mutate()}
              >
                Close
              </Button>
            )}
          </Box>
        )}
      </Box>

      {canWrite && editing && <EditRiskForm risk={risk} onDone={() => setEditing(false)} />}

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

          {risk.approval_status && (
            <>
              <Divider sx={{ my: 2 }} />
              <Grid container spacing={2}>
                <Field
                  label="Proposed Treatment"
                  value={risk.treatment_type}
                />
                <Field label="Approval Status" value={risk.approval_status} />
                <Field label="Reviewed By" value={risk.approved_by} />
                <Field label="Reviewed At" value={formatDateTime(risk.approved_at)} />
                {risk.treatment_justification && (
                  <Grid size={12}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Justification
                    </Typography>
                    <Typography variant="body2">{risk.treatment_justification}</Typography>
                  </Grid>
                )}
              </Grid>
            </>
          )}
        </CardContent>
      </Card>

      <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>
        Treatment
      </Typography>
      <Card>
        <CardContent>
          {risk.approval_status === 'pending' ? (
            user && hasRole(user.role, RISK_TREATMENT_APPROVE_ROLES) ? (
              <ReviewTreatmentForm riskId={riskId} />
            ) : (
              <Typography variant="body2" color="text.secondary">
                Awaiting approval.
              </Typography>
            )
          ) : user && hasRole(user.role, RISK_TREATMENT_PROPOSE_ROLES) ? (
            <ProposeTreatmentForm riskId={riskId} />
          ) : (
            <Typography variant="body2" color="text.secondary">
              No treatment proposed yet.
            </Typography>
          )}

          <TreatmentHistory riskId={riskId} />
        </CardContent>
      </Card>

      <Card sx={{ mt: 3 }}>
        <CardContent>
          <EvidenceSection resource="risks" resourceId={risk.id} />
        </CardContent>
      </Card>
    </Box>
  );
}
