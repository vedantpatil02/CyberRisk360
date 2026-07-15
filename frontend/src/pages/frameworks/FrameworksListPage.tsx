import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useFrameworks } from '../../hooks/useFrameworks';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';

// No DataTable here - GET /frameworks has no server-side pagination,
// sort, or filter (it's a flat 5-row list), so the generic
// paginated/sortable component's contract doesn't apply. Plain MUI
// table, same choice already made for DashboardPage's top_assets.
export function FrameworksListPage() {
  const navigate = useNavigate();
  const { data, isLoading, error } = useFrameworks();

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  if (!data) return null;

  return (
    <>
      <Typography variant="h5" gutterBottom>
        Compliance Frameworks
      </Typography>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Short Name</TableCell>
              <TableCell>Version</TableCell>
              <TableCell>Publisher</TableCell>
              <TableCell align="right">Release Year</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.length === 0 && (
              <TableRow>
                <TableCell colSpan={5}>No frameworks found.</TableCell>
              </TableRow>
            )}
            {data.map((framework) => (
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
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
}
