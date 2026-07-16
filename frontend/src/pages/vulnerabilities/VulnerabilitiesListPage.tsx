import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  FormControlLabel,
  MenuItem,
  Paper,
  Select,
  Switch,
  TextField,
  Typography,
} from '@mui/material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { usePaginatedListState } from '../../hooks/usePaginatedListState';
import { useVulnerabilities } from '../../hooks/useVulnerabilities';
import { useCreateVulnerability } from '../../hooks/useCreateVulnerability';
import { DataTable } from '../../components/DataTable/DataTable';
import type { ColumnDef } from '../../components/DataTable/DataTable.types';
import { SeverityChip } from '../../components/SeverityChip';
import { StatusChip } from '../../components/StatusChip';
import { useAuth } from '../../auth/AuthContext';
import { hasRole } from '../../api/types/auth';
import { VULNERABILITY_WRITE_ROLES } from '../../api/endpoints/vulnerabilities';
import type {
  Severity,
  Vulnerability,
  VulnerabilityCreateInput,
  VulnerabilityListParams,
  VulnerabilityStatus,
} from '../../api/types/vulnerability';

interface Filters {
  severity?: Severity;
  status?: VulnerabilityStatus;
  sla_breached?: boolean;
}

function mutationErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
  }
  return 'Something went wrong.';
}

const emptyForm: VulnerabilityCreateInput = {
  title: '',
  description: '',
  asset_id: 0,
  risk_id: 0,
  cvss_score: 0,
  owner: '',
};

function NewVulnerabilityForm({ onDone }: { onDone: () => void }) {
  const [form, setForm] = useState<VulnerabilityCreateInput>(emptyForm);
  const mutation = useCreateVulnerability();

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
          sx={{ flex: 1, minWidth: 200 }}
        />
        <TextField
          label="Asset ID"
          size="small"
          type="number"
          required
          helperText="Find the ID on the Assets page"
          value={form.asset_id || ''}
          onChange={(e) => setForm({ ...form, asset_id: Number(e.target.value) })}
          sx={{ width: 140 }}
        />
        <TextField
          label="Risk ID"
          size="small"
          type="number"
          required
          helperText="Find the ID on the Risks page"
          value={form.risk_id || ''}
          onChange={(e) => setForm({ ...form, risk_id: Number(e.target.value) })}
          sx={{ width: 140 }}
        />
        <TextField
          label="CVSS Score"
          size="small"
          type="number"
          required
          slotProps={{ htmlInput: { min: 0, max: 10, step: 0.1 } }}
          value={form.cvss_score || ''}
          onChange={(e) => setForm({ ...form, cvss_score: Number(e.target.value) })}
          sx={{ width: 140 }}
        />
        <TextField
          label="Owner"
          size="small"
          required
          value={form.owner}
          onChange={(e) => setForm({ ...form, owner: e.target.value })}
          sx={{ width: 200 }}
        />
        <TextField
          label="Description"
          size="small"
          required
          multiline
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          sx={{ flex: '1 1 100%' }}
        />
        <Button type="submit" variant="contained" disabled={mutation.isPending}>
          Create Vulnerability
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

const SEVERITIES: Severity[] = ['Critical', 'High', 'Medium', 'Low'];
const STATUSES: VulnerabilityStatus[] = ['Open', 'Closed'];

function isOverdue(row: Vulnerability): boolean {
  return row.due_date !== null && row.status === 'Open' && new Date(row.due_date) < new Date();
}

function formatDate(value: string | null): string {
  return value ? new Date(value).toLocaleDateString() : '—';
}

const columns: ColumnDef<Vulnerability>[] = [
  { id: 'id', label: 'ID', sortable: true, width: 60 },
  { id: 'title', label: 'Title', sortable: true },
  {
    id: 'severity',
    label: 'Severity',
    sortable: true,
    render: (row) => <SeverityChip severity={row.severity} />,
  },
  {
    id: 'status',
    label: 'Status',
    sortable: true,
    render: (row) => <StatusChip status={row.status} />,
  },
  { id: 'cvss_score', label: 'CVSS', sortable: true, align: 'right' },
  {
    id: 'due_date',
    label: 'Due',
    sortable: true,
    render: (row) => (
      <Typography
        variant="body2"
        color={isOverdue(row) ? 'error' : 'text.primary'}
        fontWeight={isOverdue(row) ? 600 : 400}
      >
        {formatDate(row.due_date)}
      </Typography>
    ),
  },
  { id: 'created_at', label: 'Created', render: (row) => formatDate(row.created_at) },
];

export function VulnerabilitiesListPage() {
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

  const { data, isLoading, error } = useVulnerabilities({
    limit,
    offset,
    // usePaginatedListState's sortBy is generic (plain string); the
    // DataTable columns above only ever pass one of the backend's
    // allowlisted sort_by values into it via onSortChange, so this
    // narrows to the resource-specific literal union.
    sort_by: sortBy as VulnerabilityListParams['sort_by'],
    order,
    ...filters,
  });

  const rows = (data ?? []).slice(0, pageSize);
  const hasNextPage = (data?.length ?? 0) > pageSize;

  const canWrite = user !== null && hasRole(user.role, VULNERABILITY_WRITE_ROLES);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" gutterBottom>
          Vulnerabilities
        </Typography>
        {canWrite && !showNewForm && (
          <Button variant="contained" onClick={() => setShowNewForm(true)}>
            + New Vulnerability
          </Button>
        )}
      </Box>

      {canWrite && showNewForm && (
        <NewVulnerabilityForm onDone={() => setShowNewForm(false)} />
      )}

      <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
        <Select
          size="small"
          displayEmpty
          value={filters.severity ?? ''}
          onChange={(e) =>
            setFilters({ ...filters, severity: (e.target.value || undefined) as Severity })
          }
          sx={{ minWidth: 140 }}
        >
          <MenuItem value="">All severities</MenuItem>
          {SEVERITIES.map((s) => (
            <MenuItem key={s} value={s}>
              {s}
            </MenuItem>
          ))}
        </Select>

        <Select
          size="small"
          displayEmpty
          value={filters.status ?? ''}
          onChange={(e) =>
            setFilters({ ...filters, status: (e.target.value || undefined) as VulnerabilityStatus })
          }
          sx={{ minWidth: 140 }}
        >
          <MenuItem value="">All statuses</MenuItem>
          {STATUSES.map((s) => (
            <MenuItem key={s} value={s}>
              {s}
            </MenuItem>
          ))}
        </Select>

        <FormControlLabel
          control={
            <Switch
              checked={filters.sla_breached ?? false}
              onChange={(e) =>
                setFilters({ ...filters, sla_breached: e.target.checked || undefined })
              }
            />
          }
          label="SLA breached only"
        />
      </Box>

      <DataTable
        columns={columns}
        rows={rows}
        rowKey={(row) => row.id}
        loading={isLoading}
        error={error}
        emptyMessage="No vulnerabilities found."
        onRowClick={(row) => navigate(`/vulnerabilities/${row.id}`)}
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
