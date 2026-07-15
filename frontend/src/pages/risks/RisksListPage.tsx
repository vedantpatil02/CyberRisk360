import { Box, FormControlLabel, MenuItem, Select, Switch, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { usePaginatedListState } from '../../hooks/usePaginatedListState';
import { useRisks } from '../../hooks/useRisks';
import { DataTable } from '../../components/DataTable/DataTable';
import type { ColumnDef } from '../../components/DataTable/DataTable.types';
import { SeverityChip } from '../../components/SeverityChip';
import { StatusChip } from '../../components/StatusChip';
import type { Risk, RiskLevel, RiskListParams, RiskSource, RiskStatus } from '../../api/types/risk';

interface Filters {
  risk_level?: RiskLevel;
  status?: RiskStatus;
  source?: RiskSource;
  sla_breached?: boolean;
}

const RISK_LEVELS: RiskLevel[] = ['Critical', 'High', 'Medium', 'Low'];
const STATUSES: RiskStatus[] = ['Open', 'Under Review', 'Mitigated', 'Accepted', 'Closed'];

function isOverdue(row: Risk): boolean {
  const terminal: RiskStatus[] = ['Mitigated', 'Accepted', 'Closed'];
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

export function RisksListPage() {
  const navigate = useNavigate();
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

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Risks
      </Typography>

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
