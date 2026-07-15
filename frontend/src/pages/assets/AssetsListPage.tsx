import { Box, MenuItem, Select, TextField, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { usePaginatedListState } from '../../hooks/usePaginatedListState';
import { useAssets } from '../../hooks/useAssets';
import { DataTable } from '../../components/DataTable/DataTable';
import type { ColumnDef } from '../../components/DataTable/DataTable.types';
import type { Asset, AssetListParams } from '../../api/types/asset';

interface Filters {
  criticality?: string;
  environment?: string;
  asset_type?: string;
}

// Free text, not a fixed dropdown - Asset.criticality/environment/
// asset_type are plain String columns with no enforced set of values
// (unlike Vulnerability.severity, which is derived from a fixed CVSS
// scale). Critical/High/Medium/Low is the convention used elsewhere
// in this codebase (e.g. risk_generation.py's IMPACT_BY_CRITICALITY),
// offered as a dropdown since it's the common case; environment/type
// stay free text since there's no canonical list.
const CRITICALITIES = ['Critical', 'High', 'Medium', 'Low'];

const columns: ColumnDef<Asset>[] = [
  { id: 'id', label: 'ID', sortable: true, width: 60 },
  { id: 'name', label: 'Name', sortable: true },
  { id: 'asset_type', label: 'Type' },
  { id: 'criticality', label: 'Criticality', sortable: true },
  { id: 'environment', label: 'Environment', sortable: true },
  { id: 'owner', label: 'Owner' },
  { id: 'ip_address', label: 'IP Address', render: (row) => row.ip_address ?? '—' },
];

export function AssetsListPage() {
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

  const { data, isLoading, error } = useAssets({
    limit,
    offset,
    sort_by: sortBy as AssetListParams['sort_by'],
    order,
    ...filters,
  });

  const rows = (data ?? []).slice(0, pageSize);
  const hasNextPage = (data?.length ?? 0) > pageSize;

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Assets
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
        <Select
          size="small"
          displayEmpty
          value={filters.criticality ?? ''}
          onChange={(e) => setFilters({ ...filters, criticality: e.target.value || undefined })}
          sx={{ minWidth: 140 }}
        >
          <MenuItem value="">All criticalities</MenuItem>
          {CRITICALITIES.map((c) => (
            <MenuItem key={c} value={c}>
              {c}
            </MenuItem>
          ))}
        </Select>

        <TextField
          size="small"
          placeholder="Environment"
          value={filters.environment ?? ''}
          onChange={(e) => setFilters({ ...filters, environment: e.target.value || undefined })}
          sx={{ minWidth: 140 }}
        />

        <TextField
          size="small"
          placeholder="Asset type"
          value={filters.asset_type ?? ''}
          onChange={(e) => setFilters({ ...filters, asset_type: e.target.value || undefined })}
          sx={{ minWidth: 140 }}
        />
      </Box>

      <DataTable
        columns={columns}
        rows={rows}
        rowKey={(row) => row.id}
        loading={isLoading}
        error={error}
        emptyMessage="No assets found."
        onRowClick={(row) => navigate(`/assets/${row.id}`)}
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
