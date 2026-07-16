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
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { useAudit } from '../../hooks/useAudit';
import { useUpdateAudit } from '../../hooks/useUpdateAudit';
import { useCloseAudit } from '../../hooks/useCloseAudit';
import { useAuditFindings } from '../../hooks/useAuditFindings';
import { useCreateAuditFinding } from '../../hooks/useCreateAuditFinding';
import { useUpdateAuditFinding } from '../../hooks/useUpdateAuditFinding';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { SeverityChip } from '../../components/SeverityChip';
import { StatusChip } from '../../components/StatusChip';
import { useAuth } from '../../auth/AuthContext';
import { hasRole } from '../../api/types/auth';
import { AUDIT_WRITE_ROLES } from '../../api/endpoints/audits';
import type {
  Audit,
  AuditFindingCreateInput,
  AuditFindingSeverity,
  AuditFindingStatus,
  AuditUpdateInput,
} from '../../api/types/audit';

const SEVERITIES: AuditFindingSeverity[] = ['Critical', 'High', 'Medium', 'Low'];
const FINDING_STATUSES: AuditFindingStatus[] = ['Open', 'Remediated', 'Accepted', 'Closed'];

function formatDate(value: string | null): string {
  return value ? new Date(value).toLocaleDateString() : '—';
}

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

function EditAuditForm({ audit, onDone }: { audit: Audit; onDone: () => void }) {
  const [form, setForm] = useState<AuditUpdateInput>({
    title: audit.title,
    scope: audit.scope ?? '',
    framework_id: audit.framework_id,
    lead_auditor_id: audit.lead_auditor_id,
  });
  const mutation = useUpdateAudit(audit.id);

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
        label="Framework ID"
        size="small"
        type="number"
        helperText="Find the ID on the Frameworks page"
        value={form.framework_id ?? ''}
        onChange={(e) =>
          setForm({ ...form, framework_id: e.target.value ? Number(e.target.value) : null })
        }
        sx={{ width: 160 }}
      />
      <TextField
        label="Lead Auditor User ID"
        size="small"
        type="number"
        value={form.lead_auditor_id ?? ''}
        onChange={(e) =>
          setForm({ ...form, lead_auditor_id: e.target.value ? Number(e.target.value) : null })
        }
        sx={{ width: 160 }}
      />
      <TextField
        label="Scope"
        size="small"
        value={form.scope ?? ''}
        onChange={(e) => setForm({ ...form, scope: e.target.value })}
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

const emptyFindingForm: AuditFindingCreateInput = {
  title: '',
  severity: 'Medium',
};

function NewFindingForm({ auditId, onDone }: { auditId: number; onDone: () => void }) {
  const [form, setForm] = useState<AuditFindingCreateInput>(emptyFindingForm);
  const mutation = useCreateAuditFinding(auditId);

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
        select
        label="Severity"
        size="small"
        value={form.severity}
        onChange={(e) => setForm({ ...form, severity: e.target.value as AuditFindingSeverity })}
        sx={{ minWidth: 140 }}
      >
        {SEVERITIES.map((s) => (
          <MenuItem key={s} value={s}>
            {s}
          </MenuItem>
        ))}
      </TextField>
      <TextField
        label="Control ID"
        size="small"
        type="number"
        helperText="Optional"
        value={form.control_id ?? ''}
        onChange={(e) =>
          setForm({ ...form, control_id: e.target.value ? Number(e.target.value) : null })
        }
        sx={{ width: 140 }}
      />
      <TextField
        label="Description"
        size="small"
        multiline
        value={form.description ?? ''}
        onChange={(e) => setForm({ ...form, description: e.target.value })}
        sx={{ flex: '1 1 100%' }}
      />
      <Button type="submit" variant="contained" disabled={mutation.isPending}>
        Add Finding
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

function FindingsSection({ auditId, canWrite }: { auditId: number; canWrite: boolean }) {
  const [showNewForm, setShowNewForm] = useState(false);
  const { data: findings, isLoading } = useAuditFindings(auditId);
  const updateMutation = useUpdateAuditFinding(auditId);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>
          Findings
        </Typography>
        {canWrite && !showNewForm && (
          <Button size="small" variant="contained" onClick={() => setShowNewForm(true)}>
            + Add Finding
          </Button>
        )}
      </Box>

      {canWrite && showNewForm && (
        <NewFindingForm auditId={auditId} onDone={() => setShowNewForm(false)} />
      )}

      {isLoading ? (
        <LoadingState />
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Title</TableCell>
                <TableCell>Severity</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Description</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(!findings || findings.length === 0) && (
                <TableRow>
                  <TableCell colSpan={4}>No findings recorded yet.</TableCell>
                </TableRow>
              )}
              {findings?.map((finding) => (
                <TableRow key={finding.id}>
                  <TableCell>{finding.title}</TableCell>
                  <TableCell>
                    <SeverityChip severity={finding.severity} />
                  </TableCell>
                  <TableCell>
                    {canWrite ? (
                      <Select
                        size="small"
                        value={finding.status}
                        onChange={(e) =>
                          updateMutation.mutate({
                            findingId: finding.id,
                            input: { status: e.target.value as AuditFindingStatus },
                          })
                        }
                      >
                        {FINDING_STATUSES.map((s) => (
                          <MenuItem key={s} value={s}>
                            {s}
                          </MenuItem>
                        ))}
                      </Select>
                    ) : (
                      <StatusChip status={finding.status} />
                    )}
                  </TableCell>
                  <TableCell>{finding.description ?? '—'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

export function AuditDetailPage() {
  const { id } = useParams<{ id: string }>();
  const auditId = Number(id);
  const { user } = useAuth();
  const [editing, setEditing] = useState(false);

  const { data: audit, isLoading, error } = useAudit(auditId);
  const closeMutation = useCloseAudit(auditId);

  if (isLoading) return <LoadingState />;

  if (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return (
        <Box sx={{ p: 3 }}>
          <Alert severity="warning">Audit not found.</Alert>
        </Box>
      );
    }
    return <ErrorState error={error} />;
  }

  if (!audit) return null;

  const canWrite = user !== null && hasRole(user.role, AUDIT_WRITE_ROLES);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" gutterBottom>
          {audit.title}
        </Typography>
        {canWrite && !editing && (
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button variant="outlined" onClick={() => setEditing(true)}>
              Edit
            </Button>
            {audit.status !== 'Closed' && (
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

      {canWrite && editing && <EditAuditForm audit={audit} onDone={() => setEditing(false)} />}

      <Card>
        <CardContent>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid size={{ xs: 6, sm: 4 }}>
              <Typography variant="caption" color="text.secondary" display="block">
                Status
              </Typography>
              <StatusChip status={audit.status} />
            </Grid>
            <Field label="Framework ID" value={audit.framework_id} />
            <Field label="Lead Auditor User ID" value={audit.lead_auditor_id} />
            <Field label="Start Date" value={formatDate(audit.start_date)} />
            <Field label="End Date" value={formatDate(audit.end_date)} />
            <Field label="Created" value={formatDateTime(audit.created_at)} />
            <Field label="Updated" value={formatDateTime(audit.updated_at)} />
          </Grid>

          <Divider sx={{ my: 2 }} />

          <Typography variant="subtitle2" gutterBottom>
            Scope
          </Typography>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
            {audit.scope || '—'}
          </Typography>
        </CardContent>
      </Card>

      <FindingsSection auditId={auditId} canWrite={canWrite} />
    </Box>
  );
}
