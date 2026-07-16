import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
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
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { usePendingMappings, useReviewMapping } from '../../hooks/useMappings';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { useAuth } from '../../auth/AuthContext';
import { hasRole } from '../../api/types/auth';
import { MAPPING_REVIEW_ROLES } from '../../api/endpoints/mappings';
import type { Mapping } from '../../api/types/mapping';

function mutationErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
  }
  return 'Something went wrong.';
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString();
}

function MappingRow({ mapping, canReview }: { mapping: Mapping; canReview: boolean }) {
  const navigate = useNavigate();
  const [note, setNote] = useState('');
  const mutation = useReviewMapping();

  return (
    <TableRow hover>
      <TableCell>
        <Button size="small" onClick={() => navigate(`/vulnerabilities/${mapping.vulnerability_id}`)}>
          #{mapping.vulnerability_id}
        </Button>
      </TableCell>
      <TableCell>{mapping.control_id}</TableCell>
      <TableCell>
        <Chip label={mapping.match_type ?? 'unknown'} size="small" />
      </TableCell>
      <TableCell>{mapping.matched_value ?? '—'}</TableCell>
      <TableCell align="right">
        {mapping.confidence_score != null ? mapping.confidence_score.toFixed(2) : '—'}
      </TableCell>
      <TableCell>{formatDateTime(mapping.created_at)}</TableCell>
      {canReview && (
        <TableCell align="right">
          <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', alignItems: 'center' }}>
            <TextField
              size="small"
              placeholder="Note (optional)"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              sx={{ width: 160 }}
            />
            <Button
              size="small"
              color="success"
              variant="contained"
              disabled={mutation.isPending}
              onClick={() => mutation.mutate({ id: mapping.id, approve: true, note: note || undefined })}
            >
              Approve
            </Button>
            <Button
              size="small"
              color="error"
              disabled={mutation.isPending}
              onClick={() => mutation.mutate({ id: mapping.id, approve: false, note: note || undefined })}
            >
              Reject
            </Button>
          </Box>
        </TableCell>
      )}
    </TableRow>
  );
}

export function MappingReviewPage() {
  const { user } = useAuth();
  const { data, isLoading, error } = usePendingMappings();
  const mutation = useReviewMapping();

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  if (!data) return null;

  const canReview = user !== null && hasRole(user.role, MAPPING_REVIEW_ROLES);

  return (
    <>
      <Typography variant="h5" gutterBottom>
        Mapping Review
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Vulnerability-to-control mappings suggested by the mapping engine, awaiting approval.
      </Typography>

      {mutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {mutationErrorMessage(mutation.error)}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Vulnerability</TableCell>
              <TableCell>Control ID</TableCell>
              <TableCell>Match Type</TableCell>
              <TableCell>Matched Value</TableCell>
              <TableCell align="right">Confidence</TableCell>
              <TableCell>Created</TableCell>
              {canReview && <TableCell align="right">Actions</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.length === 0 && (
              <TableRow>
                <TableCell colSpan={canReview ? 7 : 6}>No mappings awaiting review.</TableCell>
              </TableRow>
            )}
            {data.map((mapping) => (
              <MappingRow key={mapping.id} mapping={mapping} canReview={canReview} />
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
}
