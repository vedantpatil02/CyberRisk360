import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  MenuItem,
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
import { useUsers, useSetUserActive, useChangeUserRole, useAdminResetPassword } from '../../hooks/useUsers';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { ASSIGNABLE_ROLES } from '../../api/types/user';
import type { UserAccount } from '../../api/types/user';

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

function ResetPasswordControl({ userId }: { userId: number }) {
  const [open, setOpen] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const mutation = useAdminResetPassword();

  if (!open) {
    return (
      <Button size="small" onClick={() => setOpen(true)}>
        Reset Password
      </Button>
    );
  }

  return (
    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
      <TextField
        size="small"
        type="password"
        label="New password"
        value={newPassword}
        onChange={(e) => setNewPassword(e.target.value)}
      />
      <Button
        size="small"
        variant="contained"
        disabled={mutation.isPending || newPassword.length < 8}
        onClick={() =>
          mutation.mutate(
            { userId, newPassword },
            { onSuccess: () => { setOpen(false); setNewPassword(''); } },
          )
        }
      >
        Save
      </Button>
      <Button size="small" onClick={() => setOpen(false)}>
        Cancel
      </Button>
      {mutation.isError && <Alert severity="error">{mutationErrorMessage(mutation.error)}</Alert>}
    </Box>
  );
}

function UserRow({ user }: { user: UserAccount }) {
  const setActive = useSetUserActive();
  const changeRole = useChangeUserRole();

  return (
    <TableRow hover>
      <TableCell>{user.username}</TableCell>
      <TableCell>{user.email}</TableCell>
      <TableCell>
        {/* super_admin isn't in ASSIGNABLE_ROLES (backend VALID_ROLES
            excludes it - a platform role, not an org-assignable one),
            so a super-admin row can't be shown as an editable Select:
            its value wouldn't match any MenuItem and would render
            blank. Show it as a plain, non-editable chip instead. */}
        {user.role === 'super_admin' ? (
          <Chip label="super_admin" size="small" />
        ) : (
          <TextField
            select
            size="small"
            value={user.role}
            disabled={changeRole.isPending}
            onChange={(e) => changeRole.mutate({ userId: user.id, role: e.target.value })}
            sx={{ minWidth: 140 }}
          >
            {ASSIGNABLE_ROLES.map((role) => (
              <MenuItem key={role} value={role}>
                {role}
              </MenuItem>
            ))}
          </TextField>
        )}
      </TableCell>
      <TableCell>
        <Chip
          label={user.is_active ? 'Active' : 'Deactivated'}
          color={user.is_active ? 'success' : 'default'}
          size="small"
        />
      </TableCell>
      <TableCell>{formatDateTime(user.last_login)}</TableCell>
      <TableCell align="right">
        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
          <Button
            size="small"
            color={user.is_active ? 'error' : 'success'}
            disabled={setActive.isPending}
            onClick={() => setActive.mutate({ userId: user.id, active: !user.is_active })}
          >
            {user.is_active ? 'Deactivate' : 'Activate'}
          </Button>
          <ResetPasswordControl userId={user.id} />
        </Box>
      </TableCell>
    </TableRow>
  );
}

export function UsersListPage() {
  const { data, isLoading, error } = useUsers();

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  if (!data) return null;

  return (
    <>
      <Typography variant="h5" gutterBottom>
        User Management
      </Typography>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Username</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Last Login</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.length === 0 && (
              <TableRow>
                <TableCell colSpan={6}>No users found.</TableCell>
              </TableRow>
            )}
            {data.map((user) => (
              <UserRow key={user.id} user={user} />
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
}
