import { useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import DeleteIcon from '@mui/icons-material/Delete';
import axios from 'axios';
import { useAuth } from '../auth/AuthContext';
import { hasRole } from '../api/types/auth';
import { EVIDENCE_WRITE_ROLES, downloadEvidence } from '../api/endpoints/evidence';
import { useDeleteEvidence, useEvidence, useUploadEvidence } from '../hooks/useEvidence';
import { LoadingState } from './LoadingState';

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDateTime(value: string | null): string {
  return value ? new Date(value).toLocaleString() : '—';
}

function mutationErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
  }
  return 'Something went wrong.';
}

export function EvidenceSection({
  resource,
  resourceId,
}: {
  resource: 'vulnerabilities' | 'risks';
  resourceId: number;
}) {
  const { user } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [expiresAt, setExpiresAt] = useState('');

  const { data: evidence, isLoading } = useEvidence(resource, resourceId);
  const uploadMutation = useUploadEvidence(resource, resourceId);
  const deleteMutation = useDeleteEvidence(resource, resourceId);

  const canWrite = user !== null && hasRole(user.role, EVIDENCE_WRITE_ROLES);

  const handleUpload = () => {
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;
    uploadMutation.mutate(
      { file, expiresAt: expiresAt || null },
      {
        onSuccess: () => {
          if (fileInputRef.current) fileInputRef.current.value = '';
          setExpiresAt('');
        },
      },
    );
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Evidence
      </Typography>

      {canWrite && (
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap', mb: 2 }}>
          <input ref={fileInputRef} type="file" />
          <TextField
            label="Expires"
            type="date"
            size="small"
            value={expiresAt}
            onChange={(e) => setExpiresAt(e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
          />
          <Button variant="contained" disabled={uploadMutation.isPending} onClick={handleUpload}>
            Upload
          </Button>
          {uploadMutation.isError && (
            <Alert severity="error" sx={{ width: '100%' }}>
              {mutationErrorMessage(uploadMutation.error)}
            </Alert>
          )}
        </Box>
      )}

      {isLoading ? (
        <LoadingState />
      ) : (
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>File</TableCell>
                <TableCell>Size</TableCell>
                <TableCell>Uploaded</TableCell>
                <TableCell>Expires</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(!evidence || evidence.length === 0) && (
                <TableRow>
                  <TableCell colSpan={5}>No evidence attached yet.</TableCell>
                </TableRow>
              )}
              {evidence?.map((attachment) => (
                <TableRow key={attachment.id}>
                  <TableCell>{attachment.file_name}</TableCell>
                  <TableCell>{formatFileSize(attachment.file_size)}</TableCell>
                  <TableCell>{formatDateTime(attachment.uploaded_at)}</TableCell>
                  <TableCell>{formatDateTime(attachment.expires_at)}</TableCell>
                  <TableCell align="right">
                    <IconButton size="small" onClick={() => downloadEvidence(attachment)}>
                      <DownloadIcon fontSize="small" />
                    </IconButton>
                    {canWrite && (
                      <IconButton
                        size="small"
                        disabled={deleteMutation.isPending}
                        onClick={() => deleteMutation.mutate(attachment.id)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}
