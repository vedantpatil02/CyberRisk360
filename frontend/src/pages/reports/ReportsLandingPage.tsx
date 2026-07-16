import {
  List,
  ListItemButton,
  ListItemText,
  Paper,
  Typography,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useFrameworks } from '../../hooks/useFrameworks';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';

// No GET /reports list endpoint exists - there are exactly three fixed
// report types (one of them, compliance, parametrized per framework) -
// so this landing page is a static menu, not a data-driven list.
export function ReportsLandingPage() {
  const navigate = useNavigate();
  const { data: frameworks, isLoading, error } = useFrameworks();

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;

  return (
    <>
      <Typography variant="h5" gutterBottom>
        Reports
      </Typography>

      <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>
        Executive &amp; Technical
      </Typography>
      <Paper>
        <List disablePadding>
          <ListItemButton onClick={() => navigate('/reports/executive')}>
            <ListItemText
              primary="Executive Summary"
              secondary="Board-level view across assets, vulnerabilities, compliance, and risk"
            />
          </ListItemButton>
          <ListItemButton onClick={() => navigate('/reports/technical')}>
            <ListItemText
              primary="Technical Vulnerability Report"
              secondary="Full finding register grouped by severity, for analysts"
            />
          </ListItemButton>
        </List>
      </Paper>

      <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>
        Compliance Assessment
      </Typography>
      <Paper>
        <List disablePadding>
          {(frameworks ?? []).length === 0 && (
            <ListItemText sx={{ p: 2 }} primary="No frameworks found." />
          )}
          {(frameworks ?? []).map((framework) => (
            <ListItemButton
              key={framework.id}
              onClick={() => navigate(`/reports/compliance/${framework.short_name}`)}
            >
              <ListItemText primary={framework.name} secondary={framework.version} />
            </ListItemButton>
          ))}
        </List>
      </Paper>
    </>
  );
}
