import { Alert, AlertTitle, Box } from '@mui/material';
import type { Role } from '../api/types/auth';

interface AccessDeniedProps {
  currentRole: Role;
  requiredRoles: readonly Role[];
}

// Rendered in place (not a redirect) when a logged-in user's role
// doesn't have access to a given page - the backend itself returns
// 403 (not a session failure) in this situation, so the frontend
// mirrors that distinction rather than treating it as a logout.
export function AccessDenied({ currentRole, requiredRoles }: AccessDeniedProps) {
  return (
    <Box sx={{ p: 3 }}>
      <Alert severity="warning">
        <AlertTitle>Access denied</AlertTitle>
        Your role (<strong>{currentRole}</strong>) doesn&apos;t have access to this page. Required
        role: {requiredRoles.join(', ')}.
      </Alert>
    </Box>
  );
}
