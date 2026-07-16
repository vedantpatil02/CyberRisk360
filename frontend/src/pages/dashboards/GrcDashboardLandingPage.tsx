import { List, ListItemButton, ListItemText, Paper, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useFrameworks } from '../../hooks/useFrameworks';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';

// No GET /dashboard/grc list endpoint exists - one dashboard per
// framework, so this picker (same idiom as ReportsLandingPage's
// compliance-framework list) is the entry point.
export function GrcDashboardLandingPage() {
  const navigate = useNavigate();
  const { data: frameworks, isLoading, error } = useFrameworks();

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;

  return (
    <>
      <Typography variant="h5" gutterBottom>
        GRC Dashboard
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Select a framework to view its compliance posture and risk.
      </Typography>
      <Paper>
        <List disablePadding>
          {(frameworks ?? []).length === 0 && (
            <ListItemText sx={{ p: 2 }} primary="No frameworks found." />
          )}
          {(frameworks ?? []).map((framework) => (
            <ListItemButton
              key={framework.id}
              onClick={() => navigate(`/grc-dashboard/${framework.short_name}`)}
            >
              <ListItemText primary={framework.name} secondary={framework.version} />
            </ListItemButton>
          ))}
        </List>
      </Paper>
    </>
  );
}
