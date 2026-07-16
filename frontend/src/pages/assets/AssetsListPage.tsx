import { useState } from 'react';
import { Alert, Box, Button, MenuItem, Paper, Select, TextField, Typography } from '@mui/material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { usePaginatedListState } from '../../hooks/usePaginatedListState';
import { useAssets } from '../../hooks/useAssets';
import { useCreateAsset } from '../../hooks/useCreateAsset';
import { DataTable } from '../../components/DataTable/DataTable';
import type { ColumnDef } from '../../components/DataTable/DataTable.types';
import { useAuth } from '../../auth/AuthContext';
import { hasRole } from '../../api/types/auth';
import { ASSET_WRITE_ROLES } from '../../api/endpoints/assets';
import type { Asset, AssetCreateInput, AssetListParams } from '../../api/types/asset';

interface Filters {
  criticality?: string;
  environment?: string;
  asset_type?: string;
}

function mutationErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
  }
  return 'Something went wrong.';
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

const emptyForm: AssetCreateInput = {
  name: '',
  asset_type: '',
  owner: '',
  criticality: 'Medium',
  environment: '',
};

function NewAssetForm({ onDone }: { onDone: () => void }) {
  const [form, setForm] = useState<AssetCreateInput>(emptyForm);
  const mutation = useCreateAsset();

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
          label="Name"
          size="small"
          required
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          sx={{ minWidth: 180 }}
        />
        <TextField
          label="Type"
          size="small"
          required
          value={form.asset_type}
          onChange={(e) => setForm({ ...form, asset_type: e.target.value })}
          sx={{ minWidth: 140 }}
        />
        <Select
          size="small"
          value={form.criticality}
          onChange={(e) => setForm({ ...form, criticality: e.target.value })}
          sx={{ minWidth: 140 }}
        >
          {CRITICALITIES.map((c) => (
            <MenuItem key={c} value={c}>
              {c}
            </MenuItem>
          ))}
        </Select>
        <TextField
          label="Environment"
          size="small"
          required
          value={form.environment}
          onChange={(e) => setForm({ ...form, environment: e.target.value })}
          sx={{ minWidth: 140 }}
        />
        <TextField
          label="Owner"
          size="small"
          required
          value={form.owner}
          onChange={(e) => setForm({ ...form, owner: e.target.value })}
          sx={{ minWidth: 140 }}
        />
        <TextField
          label="IP Address"
          size="small"
          value={form.ip_address ?? ''}
          onChange={(e) => setForm({ ...form, ip_address: e.target.value || null })}
          sx={{ minWidth: 140 }}
        />
        <Button type="submit" variant="contained" disabled={mutation.isPending}>
          Create Asset
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

export function AssetsListPage() {
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

  const { data, isLoading, error } = useAssets({
    limit,
    offset,
    sort_by: sortBy as AssetListParams['sort_by'],
    order,
    ...filters,
  });

  const rows = (data ?? []).slice(0, pageSize);
  const hasNextPage = (data?.length ?? 0) > pageSize;

  const canWrite = user !== null && hasRole(user.role, ASSET_WRITE_ROLES);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" gutterBottom>
          Assets
        </Typography>
        {canWrite && !showNewForm && (
          <Button variant="contained" onClick={() => setShowNewForm(true)}>
            + New Asset
          </Button>
        )}
      </Box>

      {canWrite && showNewForm && <NewAssetForm onDone={() => setShowNewForm(false)} />}

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
