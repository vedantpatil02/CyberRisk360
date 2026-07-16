import { useState } from 'react';
import { Alert, Box, Button, MenuItem, Paper, Select, TextField, Typography } from '@mui/material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { usePaginatedListState } from '../../hooks/usePaginatedListState';
import { useAudits } from '../../hooks/useAudits';
import { useCreateAudit } from '../../hooks/useCreateAudit';
import { DataTable } from '../../components/DataTable/DataTable';
import type { ColumnDef } from '../../components/DataTable/DataTable.types';
import { StatusChip } from '../../components/StatusChip';
import { useAuth } from '../../auth/AuthContext';
import { hasRole } from '../../api/types/auth';
import { AUDIT_WRITE_ROLES } from '../../api/endpoints/audits';
import type { Audit, AuditCreateInput, AuditListParams, AuditStatus } from '../../api/types/audit';

interface Filters {
  status?: AuditStatus;
}

const STATUSES: AuditStatus[] = ['Planned', 'In Progress', 'Completed', 'Closed'];

function formatDate(value: string | null): string {
  return value ? new Date(value).toLocaleDateString() : '—';
}

function mutationErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
  }
  return 'Something went wrong.';
}

const columns: ColumnDef<Audit>[] = [
  { id: 'id', label: 'ID', sortable: true, width: 60 },
  { id: 'title', label: 'Title', sortable: true },
  {
    id: 'status',
    label: 'Status',
    sortable: true,
    render: (row) => <StatusChip status={row.status} />,
  },
  { id: 'start_date', label: 'Start', sortable: true, render: (row) => formatDate(row.start_date) },
  { id: 'end_date', label: 'End', sortable: true, render: (row) => formatDate(row.end_date) },
];

const emptyForm: AuditCreateInput = {
  title: '',
  scope: '',
};

function NewAuditForm({ onDone }: { onDone: () => void }) {
  const [form, setForm] = useState<AuditCreateInput>(emptyForm);
  const mutation = useCreateAudit();

  return (
    <Paper
      component="form"
      sx={{ p: 2, mb: 2 }}
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate(form, { onSuccess: onDone });
      }}
    >
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          label="Title"
          size="small"
          required
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          sx={{ flex: 1, minWidth: 240 }}
        />
        <TextField
          label="Scope"
          size="small"
          value={form.scope ?? ''}
          onChange={(e) => setForm({ ...form, scope: e.target.value })}
          sx={{ flex: 1, minWidth: 240 }}
        />
        <Button type="submit" variant="contained" disabled={mutation.isPending}>
          Create Audit
        </Button>
        <Button onClick={onDone}>Cancel</Button>
        {mutation.isError && (
          <Alert severity="error" sx={{ width: '100%' }}>
            {mutationErrorMessage(mutation.error)}
          </Alert>
        )}
      </Box>
    </Paper>
  );
}

export function AuditsListPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [showNewForm, setShowNewForm] = useState(false);
  const {
    page,
    pageSize,
    sortBy,
    order,
    filters,
    offset,
    limit,
    setPage,
    setPageSize,
    setSort,
    setFilters,
  } = usePaginatedListState<Filters>({ defaultSortBy: 'id' });

  const { data, isLoading, error } = useAudits({
    limit,
    offset,
    sort_by: sortBy as AuditListParams['sort_by'],
    order,
    ...filters,
  });

  const rows = (data ?? []).slice(0, pageSize);
  const hasNextPage = (data?.length ?? 0) > pageSize;

  const canWrite = user !== null && hasRole(user.role, AUDIT_WRITE_ROLES);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" gutterBottom>
          Audits
        </Typography>
        {canWrite && !showNewForm && (
          <Button variant="contained" onClick={() => setShowNewForm(true)}>
            + New Audit
          </Button>
        )}
      </Box>

      {canWrite && showNewForm && <NewAuditForm onDone={() => setShowNewForm(false)} />}

      <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
        <Select
          size="small"
          displayEmpty
          value={filters.status ?? ''}
          onChange={(e) =>
            setFilters({ ...filters, status: (e.target.value || undefined) as AuditStatus })
          }
          sx={{ minWidth: 160 }}
        >
          <MenuItem value="">All statuses</MenuItem>
          {STATUSES.map((s) => (
            <MenuItem key={s} value={s}>
              {s}
            </MenuItem>
          ))}
        </Select>
      </Box>

      <DataTable
        columns={columns}
        rows={rows}
        rowKey={(row) => row.id}
        loading={isLoading}
        error={error}
        emptyMessage="No audits found."
        onRowClick={(row) => navigate(`/audits/${row.id}`)}
        sortBy={sortBy}
        order={order}
        onSortChange={setSort}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
        hasNextPage={hasNextPage}
      />
    </Box>
  );
}
