import { useState, type FormEvent } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import {
  Alert,
  Box,
  Button,
  Container,
  Link,
  MenuItem,
  Paper,
  TextField,
  Typography,
  CircularProgress,
} from '@mui/material';
import { registerUser } from '../api/endpoints/users';
import { ASSIGNABLE_ROLES } from '../api/types/user';
import type { RegisterInput } from '../api/types/user';

function registerErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
  }
  return 'Registration failed. Please try again.';
}

const emptyForm: RegisterInput = {
  username: '',
  email: '',
  password: '',
  role: 'analyst',
  org_slug: '',
};

export function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<RegisterInput>(emptyForm);

  const mutation = useMutation({
    mutationFn: () =>
      registerUser({ ...form, org_slug: form.org_slug || undefined }),
    onSuccess: () => navigate('/login', { replace: true }),
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }

  return (
    <Container maxWidth="xs">
      <Box sx={{ mt: 8 }}>
        <Paper sx={{ p: 4 }}>
          <Typography variant="h5" gutterBottom>
            Create Account
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Join CyberRisk360
          </Typography>

          {mutation.isError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {registerErrorMessage(mutation.error)}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              label="Username"
              fullWidth
              required
              margin="normal"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              autoFocus
            />
            <TextField
              label="Email"
              type="email"
              fullWidth
              required
              margin="normal"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
            <TextField
              label="Password"
              type="password"
              fullWidth
              required
              margin="normal"
              helperText="At least 8 characters"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
            <TextField
              select
              label="Role"
              fullWidth
              margin="normal"
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value as RegisterInput['role'] })}
            >
              {ASSIGNABLE_ROLES.map((role) => (
                <MenuItem key={role} value={role}>
                  {role}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Organization slug"
              fullWidth
              margin="normal"
              helperText="Leave blank to join the default organization"
              value={form.org_slug}
              onChange={(e) => setForm({ ...form, org_slug: e.target.value })}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3 }}
              disabled={mutation.isPending}
            >
              {mutation.isPending ? <CircularProgress size={24} /> : 'Create account'}
            </Button>
            <Typography variant="body2" sx={{ mt: 2, textAlign: 'center' }}>
              Already have an account?{' '}
              <Link component={RouterLink} to="/login">
                Sign in
              </Link>
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}
