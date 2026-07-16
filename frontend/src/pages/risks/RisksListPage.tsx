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
import { useRisks } from '../../hooks/useRisks';
import { useCreateRisk } from '../../hooks/useCreateRisk';
import { DataTable } from '../../components/DataTable/DataTable';
import type { ColumnDef } from '../../components/DataTable/DataTable.types';
import { SeverityChip } from '../../components/SeverityChip';
import { StatusChip } from '../../components/StatusChip';
import { useAuth } from '../../auth/AuthContext';
import { hasRole } from '../../api/types/auth';
import { RISK_WRITE_ROLES } from '../../api/endpoints/risks';
import type {
  Risk,
  RiskCreateInput,
  RiskLevel,
  RiskListParams,
  RiskSource,
  RiskStatus,
} from '../../api/types/risk';

interface Filters {
  risk_level?: RiskLevel;
  status?: RiskStatus;
  source?: RiskSource;
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

const RISK_LEVELS: RiskLevel[] = ['Critical', 'High', 'Medium', 'Low'];
const STATUSES: RiskStatus[] = ['Open', 'Under Review', 'Mitigated', 'Accepted', 'Closed'];

function isOverdue(row: Risk): boolean {
  const terminal: RiskStatus[] = ['Mitigated', 'Accepted', 'Transferred', 'Avoided', 'Closed'];
  return (
    row.due_date !== null && !terminal.includes(row.status) && new Date(row.due_date) < new Date()
  );
}

function formatDate(value: string | null): string {
  return value ? new Date(value).toLocaleDateString() : '—';
}

const columns: ColumnDef<Risk>[] = [
  { id: 'id', label: 'ID', sortable: true, width: 60 },
  { id: 'title', label: 'Title' },
  {
    id: 'risk_level',
    label: 'Level',
    sortable: true,
    render: (row) => (row.risk_level ? <SeverityChip severity={row.risk_level} /> : '—'),
  },
  {
    id: 'status',
    label: 'Status',
    sortable: true,
    render: (row) => <StatusChip status={row.status} />,
  },
  { id: 'risk_score', label: 'Score', sortable: true, align: 'right' },
  { id: 'source', label: 'Source' },
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
];

const emptyForm: RiskCreateInput = {
  title: '',
  description: '',
  asset_id: 0,
  impact: 3,
  likelihood: 3,
  owner: '',
};

function NewRiskForm({ onDone }: { onDone: () => void }) {
  const [form, setForm] = useState<RiskCreateInput>(emptyForm);
  const mutation = useCreateRisk();

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
          label="Impact (1-5)"
          size="small"
          type="number"
          required
          slotProps={{ htmlInput: { min: 1, max: 5 } }}
          value={form.impact}
          onChange={(e) => setForm({ ...form, impact: Number(e.target.value) })}
          sx={{ width: 140 }}
        />
        <TextField
          label="Likelihood (1-5)"
          size="small"
          type="number"
          required
          slotProps={{ htmlInput: { min: 1, max: 5 } }}
          value={form.likelihood}
          onChange={(e) => setForm({ ...form, likelihood: Number(e.target.value) })}
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
          Create Risk
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

export function RisksListPage() {
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

  const { data, isLoading, error } = useRisks({
    limit,
    offset,
    sort_by: sortBy as RiskListParams['sort_by'],
    order,
    ...filters,
  });

  const rows = (data ?? []).slice(0, pageSize);
  const hasNextPage = (data?.length ?? 0) > pageSize;

  const canWrite = user !== null && hasRole(user.role, RISK_WRITE_ROLES);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" gutterBottom>
          Risks
        </Typography>
        {canWrite && !showNewForm && (
          <Button variant="contained" onClick={() => setShowNewForm(true)}>
            + New Risk
          </Button>
        )}
      </Box>

      {canWrite && showNewForm && <NewRiskForm onDone={() => setShowNewForm(false)} />}

      <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
        <Select
          size="small"
          displayEmpty
          value={filters.risk_level ?? ''}
          onChange={(e) =>
            setFilters({ ...filters, risk_level: (e.target.value || undefined) as RiskLevel })
          }
          sx={{ minWidth: 140 }}
        >
          <MenuItem value="">All levels</MenuItem>
          {RISK_LEVELS.map((l) => (
            <MenuItem key={l} value={l}>
              {l}
            </MenuItem>
          ))}
        </Select>

        <Select
          size="small"
          displayEmpty
          value={filters.status ?? ''}
          onChange={(e) =>
            setFilters({ ...filters, status: (e.target.value || undefined) as RiskStatus })
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

        <Select
          size="small"
          displayEmpty
          value={filters.source ?? ''}
          onChange={(e) =>
            setFilters({ ...filters, source: (e.target.value || undefined) as RiskSource })
          }
          sx={{ minWidth: 120 }}
        >
          <MenuItem value="">All sources</MenuItem>
          <MenuItem value="manual">Manual</MenuItem>
          <MenuItem value="auto">Auto</MenuItem>
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
        emptyMessage="No risks found."
        onRowClick={(row) => navigate(`/risks/${row.id}`)}
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
