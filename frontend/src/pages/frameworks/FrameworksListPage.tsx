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
import { useNavigate } from 'react-router-dom';
import { useFrameworks } from '../../hooks/useFrameworks';
import { useCreateFramework } from '../../hooks/useCreateFramework';
import { useUpdateFramework } from '../../hooks/useUpdateFramework';
import { useDeleteFramework } from '../../hooks/useDeleteFramework';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { useAuth } from '../../auth/AuthContext';
import { hasRole } from '../../api/types/auth';
import { FRAMEWORK_WRITE_ROLES } from '../../api/endpoints/frameworks';
import type { Framework, FrameworkCreateInput, FrameworkUpdateInput } from '../../api/types/framework';

function mutationErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
  }
  return 'Something went wrong.';
}

const emptyForm: FrameworkCreateInput = {
  name: '',
  short_name: '',
  version: '',
  publisher: '',
};

function NewFrameworkForm({ onDone }: { onDone: () => void }) {
  const [form, setForm] = useState<FrameworkCreateInput>(emptyForm);
  const mutation = useCreateFramework();

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
          label="Short Name"
          size="small"
          required
          value={form.short_name}
          onChange={(e) => setForm({ ...form, short_name: e.target.value })}
          sx={{ minWidth: 140 }}
        />
        <TextField
          label="Version"
          size="small"
          required
          value={form.version}
          onChange={(e) => setForm({ ...form, version: e.target.value })}
          sx={{ minWidth: 120 }}
        />
        <TextField
          label="Publisher"
          size="small"
          required
          value={form.publisher}
          onChange={(e) => setForm({ ...form, publisher: e.target.value })}
          sx={{ minWidth: 160 }}
        />
        <TextField
          label="Release Year"
          size="small"
          type="number"
          value={form.release_year ?? ''}
          onChange={(e) =>
            setForm({ ...form, release_year: e.target.value ? Number(e.target.value) : null })
          }
          sx={{ width: 140 }}
        />
        <Button type="submit" variant="contained" disabled={mutation.isPending}>
          Create Framework
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

function EditFrameworkRow({ framework, onDone }: { framework: Framework; onDone: () => void }) {
  const [form, setForm] = useState<FrameworkUpdateInput>({
    name: framework.name,
    version: framework.version,
    publisher: framework.publisher,
    release_year: framework.release_year,
  });
  const mutation = useUpdateFramework(framework.id);

  return (
    <TableRow>
      <TableCell>
        <TextField
          size="small"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
      </TableCell>
      <TableCell>{framework.short_name}</TableCell>
      <TableCell>
        <TextField
          size="small"
          value={form.version}
          onChange={(e) => setForm({ ...form, version: e.target.value })}
        />
      </TableCell>
      <TableCell>
        <TextField
          size="small"
          value={form.publisher}
          onChange={(e) => setForm({ ...form, publisher: e.target.value })}
        />
      </TableCell>
      <TableCell align="right">
        <TextField
          size="small"
          type="number"
          value={form.release_year ?? ''}
          onChange={(e) =>
            setForm({ ...form, release_year: e.target.value ? Number(e.target.value) : null })
          }
          sx={{ width: 100 }}
        />
      </TableCell>
      <TableCell align="right">
        <Button
          size="small"
          variant="contained"
          disabled={mutation.isPending}
          onClick={(e) => {
            e.stopPropagation();
            mutation.mutate(form, { onSuccess: onDone });
          }}
        >
          Save
        </Button>
        <Button
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            onDone();
          }}
        >
          Cancel
        </Button>
        {mutation.isError && (
          <Alert severity="error" sx={{ mt: 1 }}>
            {mutationErrorMessage(mutation.error)}
          </Alert>
        )}
      </TableCell>
    </TableRow>
  );
}

function FrameworkRowActions({
  framework,
  onEdit,
}: {
  framework: Framework;
  onEdit: () => void;
}) {
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const mutation = useDeleteFramework();

  if (confirmingDelete) {
    return (
      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
        <Typography variant="body2" color="error" sx={{ alignSelf: 'center' }}>
          Delete?
        </Typography>
        <Button
          size="small"
          color="error"
          variant="contained"
          disabled={mutation.isPending}
          onClick={(e) => {
            e.stopPropagation();
            mutation.mutate(framework.id, { onSuccess: () => setConfirmingDelete(false) });
          }}
        >
          Yes
        </Button>
        <Button
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            setConfirmingDelete(false);
          }}
        >
          Cancel
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
      <Button
        size="small"
        onClick={(e) => {
          e.stopPropagation();
          onEdit();
        }}
      >
        Edit
      </Button>
      <Button
        size="small"
        color="error"
        onClick={(e) => {
          e.stopPropagation();
          setConfirmingDelete(true);
        }}
      >
        Delete
      </Button>
    </Box>
  );
}

// No DataTable here - GET /frameworks has no server-side pagination,
// sort, or filter (it's a flat 5-row list), so the generic
// paginated/sortable component's contract doesn't apply. Plain MUI
// table, same choice already made for DashboardPage's top_assets.
export function FrameworksListPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [showNewForm, setShowNewForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const { data, isLoading, error } = useFrameworks();

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  if (!data) return null;

  const canWrite = user !== null && hasRole(user.role, FRAMEWORK_WRITE_ROLES);

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" gutterBottom>
          Compliance Frameworks
        </Typography>
        {canWrite && !showNewForm && (
          <Button variant="contained" onClick={() => setShowNewForm(true)}>
            + New Framework
          </Button>
        )}
      </Box>

      {canWrite && showNewForm && <NewFrameworkForm onDone={() => setShowNewForm(false)} />}

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Short Name</TableCell>
              <TableCell>Version</TableCell>
              <TableCell>Publisher</TableCell>
              <TableCell align="right">Release Year</TableCell>
              {canWrite && <TableCell align="right">Actions</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.length === 0 && (
              <TableRow>
                <TableCell colSpan={canWrite ? 6 : 5}>No frameworks found.</TableCell>
              </TableRow>
            )}
            {data.map((framework) =>
              editingId === framework.id ? (
                <EditFrameworkRow
                  key={framework.id}
                  framework={framework}
                  onDone={() => setEditingId(null)}
                />
              ) : (
                <TableRow
                  key={framework.id}
                  hover
                  onClick={() => navigate(`/frameworks/${framework.short_name}`)}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell>{framework.name}</TableCell>
                  <TableCell>{framework.short_name}</TableCell>
                  <TableCell>{framework.version}</TableCell>
                  <TableCell>{framework.publisher}</TableCell>
                  <TableCell align="right">{framework.release_year ?? '—'}</TableCell>
                  {canWrite && (
                    <TableCell align="right">
                      <FrameworkRowActions
                        framework={framework}
                        onEdit={() => setEditingId(framework.id)}
                      />
                    </TableCell>
                  )}
                </TableRow>
              ),
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
}
