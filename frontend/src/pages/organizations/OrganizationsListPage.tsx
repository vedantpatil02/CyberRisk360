import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
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
import axios from 'axios';
import { useCreateOrganization, useOrganizations } from '../../hooks/useOrganizations';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import type { OrganizationCreateInput } from '../../api/types/organization';

function mutationErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
  }
  return 'Something went wrong.';
}

function formatDateTime(value: string | null): string {
  return value ? new Date(value).toLocaleString() : '—';
}

const emptyForm: OrganizationCreateInput = { name: '', slug: '' };

function NewOrganizationForm({ onDone }: { onDone: () => void }) {
  const [form, setForm] = useState<OrganizationCreateInput>(emptyForm);
  const mutation = useCreateOrganization();

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
          sx={{ minWidth: 200 }}
        />
        <TextField
          label="Slug"
          size="small"
          required
          helperText="lowercase letters, numbers, hyphens"
          value={form.slug}
          onChange={(e) => setForm({ ...form, slug: e.target.value })}
          sx={{ minWidth: 200 }}
        />
        <Button type="submit" variant="contained" disabled={mutation.isPending}>
          Create Organization
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

export function OrganizationsListPage() {
  const [showNewForm, setShowNewForm] = useState(false);
  const { data, isLoading, error } = useOrganizations();

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  if (!data) return null;

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" gutterBottom>
          Organizations
        </Typography>
        {!showNewForm && (
          <Button variant="contained" onClick={() => setShowNewForm(true)}>
            + New Organization
          </Button>
        )}
      </Box>

      {showNewForm && <NewOrganizationForm onDone={() => setShowNewForm(false)} />}

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Slug</TableCell>
              <TableCell>Created</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.length === 0 && (
              <TableRow>
                <TableCell colSpan={3}>No organizations found.</TableCell>
              </TableRow>
            )}
            {data.map((org) => (
              <TableRow key={org.id}>
                <TableCell>{org.name}</TableCell>
                <TableCell>{org.slug}</TableCell>
                <TableCell>{formatDateTime(org.created_at)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
}
