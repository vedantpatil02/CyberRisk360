import { useState, type FormEvent } from 'react';
import { useNavigate, useLocation, Navigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import {
  Alert,
  Box,
  Button,
  Container,
  Paper,
  TextField,
  Typography,
  CircularProgress,
} from '@mui/material';
import { login } from '../api/endpoints/auth';
import { useAuth } from '../auth/AuthContext';

interface LocationState {
  from?: { pathname: string };
}

function loginErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 429) {
      return 'Too many login attempts. Try again in a minute.';
    }
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
  }
  return 'Login failed. Please try again.';
}

export function LoginPage() {
  const { isAuthenticated, login: setSession } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const mutation = useMutation({
    mutationFn: () => login(email, password),
    // POST /login is rate-limited to 5/minute/IP on the backend -
    // retrying automatically would silently burn that budget.
    retry: false,
    onSuccess: (data) => {
      setSession(data.access_token);
      const state = location.state as LocationState | null;
      navigate(state?.from?.pathname ?? '/dashboard', { replace: true });
    },
  });

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }

  return (
    <Container maxWidth="xs">
      <Box sx={{ mt: 12 }}>
        <Paper sx={{ p: 4 }}>
          <Typography variant="h5" gutterBottom>
            CyberRisk360
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Sign in to continue
          </Typography>

          {mutation.isError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {loginErrorMessage(mutation.error)}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              label="Email"
              type="email"
              fullWidth
              required
              margin="normal"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoFocus
            />
            <TextField
              label="Password"
              type="password"
              fullWidth
              required
              margin="normal"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3 }}
              disabled={mutation.isPending}
            >
              {mutation.isPending ? <CircularProgress size={24} /> : 'Sign in'}
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}
