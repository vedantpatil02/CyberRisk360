import { useState, type FormEvent } from 'react';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { Alert, Box, Button, Card, CardContent, TextField, Typography } from '@mui/material';
import { changeOwnPassword } from '../api/endpoints/users';
import { useAuth } from '../auth/AuthContext';

function mutationErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
  }
  return 'Something went wrong.';
}

export function AccountPage() {
  const { user } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const mutation = useMutation({
    mutationFn: () =>
      changeOwnPassword({ current_password: currentPassword, new_password: newPassword }),
    onSuccess: () => {
      setCurrentPassword('');
      setNewPassword('');
    },
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }

  return (
    <Box sx={{ maxWidth: 480 }}>
      <Typography variant="h5" gutterBottom>
        My Account
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {user?.email} ({user?.role})
      </Typography>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Change Password
          </Typography>

          {mutation.isSuccess && (
            <Alert severity="success" sx={{ mb: 2 }}>
              Password changed.
            </Alert>
          )}
          {mutation.isError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {mutationErrorMessage(mutation.error)}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              label="Current password"
              type="password"
              fullWidth
              required
              margin="normal"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
            />
            <TextField
              label="New password"
              type="password"
              fullWidth
              required
              margin="normal"
              helperText="At least 8 characters"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <Button
              type="submit"
              variant="contained"
              sx={{ mt: 2 }}
              disabled={mutation.isPending || newPassword.length < 8}
            >
              Save
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
