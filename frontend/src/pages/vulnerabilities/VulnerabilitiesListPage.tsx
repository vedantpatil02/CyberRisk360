import { Box, FormControlLabel, MenuItem, Select, Switch, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { usePaginatedListState } from '../../hooks/usePaginatedListState';
import { useVulnerabilities } from '../../hooks/useVulnerabilities';
import { DataTable } from '../../components/DataTable/DataTable';
import type { ColumnDef } from '../../components/DataTable/DataTable.types';
import { SeverityChip } from '../../components/SeverityChip';
import { StatusChip } from '../../components/StatusChip';
import type {
  Severity,
  Vulnerability,
  VulnerabilityListParams,
  VulnerabilityStatus,
} from '../../api/types/vulnerability';

interface Filters {
  severity?: Severity;
  status?: VulnerabilityStatus;
  sla_breached?: boolean;
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

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Vulnerabilities
      </Typography>

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
