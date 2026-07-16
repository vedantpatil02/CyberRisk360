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
import { useAsset } from '../../hooks/useAsset';
import { useAssetSummary } from '../../hooks/useAssetSummary';
import { useAssetVulnerabilities } from '../../hooks/useAssetVulnerabilities';
import { useUpdateAsset } from '../../hooks/useUpdateAsset';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { severityColors } from '../../theme';
import { useAuth } from '../../auth/AuthContext';
import { hasRole } from '../../api/types/auth';
import { ASSET_WRITE_ROLES } from '../../api/endpoints/assets';
import type { Asset, AssetUpdateInput } from '../../api/types/asset';

const CRITICALITIES = ['Critical', 'High', 'Medium', 'Low'];

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <Paper sx={{ p: 2, textAlign: 'center', borderTop: 4, borderColor: severityColors[label] }}>
      <Typography variant="h5">{value}</Typography>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
    </Paper>
  );
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

function EditAssetForm({ asset, onDone }: { asset: Asset; onDone: () => void }) {
  const [form, setForm] = useState<AssetUpdateInput>({
    name: asset.name,
    asset_type: asset.asset_type,
    owner: asset.owner,
    criticality: asset.criticality,
    ip_address: asset.ip_address,
    environment: asset.environment,
  });
  const mutation = useUpdateAsset(asset.id);

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
        label="Name"
        size="small"
        value={form.name}
        onChange={(e) => setForm({ ...form, name: e.target.value })}
        sx={{ minWidth: 180 }}
      />
      <TextField
        label="Type"
        size="small"
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
        value={form.environment}
        onChange={(e) => setForm({ ...form, environment: e.target.value })}
        sx={{ minWidth: 140 }}
      />
      <TextField
        label="Owner"
        size="small"
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

export function AssetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const assetId = Number(id);
  const { user } = useAuth();
  const [editing, setEditing] = useState(false);

  const { data: asset, isLoading: assetLoading, error: assetError } = useAsset(assetId);
  const { data: summary, isLoading, error } = useAssetSummary(assetId);
  const { data: vulnerabilities, isLoading: vulnsLoading } = useAssetVulnerabilities(assetId);

  if (isLoading || assetLoading) return <LoadingState />;

  if (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return (
        <Box sx={{ p: 3 }}>
          <Alert severity="warning">Asset not found.</Alert>
        </Box>
      );
    }
    return <ErrorState error={error} />;
  }

  if (assetError && !(axios.isAxiosError(assetError) && assetError.response?.status === 404)) {
    return <ErrorState error={assetError} />;
  }

  if (!summary) return null;

  const canWrite = user !== null && hasRole(user.role, ASSET_WRITE_ROLES);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" gutterBottom>
          {summary.asset_name}
        </Typography>
        {canWrite && asset && !editing && (
          <Button variant="outlined" onClick={() => setEditing(true)}>
            Edit
          </Button>
        )}
      </Box>

      {canWrite && asset && editing && (
        <EditAssetForm asset={asset} onDone={() => setEditing(false)} />
      )}

      {asset && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={2}>
              <Field label="Type" value={asset.asset_type} />
              <Field label="Criticality" value={asset.criticality} />
              <Field label="Environment" value={asset.environment} />
              <Field label="Owner" value={asset.owner} />
              <Field label="IP Address" value={asset.ip_address} />
            </Grid>
          </CardContent>
        </Card>
      )}

      <Divider sx={{ mb: 3 }} />

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Critical" value={summary.critical} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="High" value={summary.high} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Medium" value={summary.medium} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatCard label="Low" value={summary.low} />
        </Grid>
      </Grid>

      <Typography variant="h6" gutterBottom>
        Vulnerabilities ({summary.total})
      </Typography>
      {vulnsLoading ? (
        <LoadingState />
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Title</TableCell>
                <TableCell>Severity</TableCell>
                <TableCell align="right">CVSS</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(!vulnerabilities || vulnerabilities.length === 0) && (
                <TableRow>
                  <TableCell colSpan={4}>No vulnerabilities on this asset.</TableCell>
                </TableRow>
              )}
              {vulnerabilities?.map((vuln) => (
                <TableRow key={vuln.id}>
                  <TableCell>{vuln.title}</TableCell>
                  <TableCell>{vuln.severity}</TableCell>
                  <TableCell align="right">{vuln.cvss_score}</TableCell>
                  <TableCell>{vuln.status}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}
