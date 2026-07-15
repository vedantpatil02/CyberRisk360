import { Box, IconButton, MenuItem, Select, Typography } from '@mui/material';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';

const PAGE_SIZE_OPTIONS = [25, 50, 100];

interface PagerProps {
  page: number;
  pageSize: number;
  hasNextPage: boolean;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}

// Custom pager instead of MUI's TablePagination/DataGrid: both assume
// a known total row count, which this API never provides (bare-array
// responses, no {items,total} envelope anywhere) - see
// DataTable.types.ts's hasNextPage comment.
export function Pager({ page, pageSize, hasNextPage, onPageChange, onPageSizeChange }: PagerProps) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 2, p: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="body2">Rows per page</Typography>
        <Select
          size="small"
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
        >
          {PAGE_SIZE_OPTIONS.map((size) => (
            <MenuItem key={size} value={size}>
              {size}
            </MenuItem>
          ))}
        </Select>
      </Box>

      <Typography variant="body2">Page {page + 1}</Typography>

      <Box>
        <IconButton size="small" disabled={page === 0} onClick={() => onPageChange(page - 1)}>
          <ChevronLeftIcon />
        </IconButton>
        <IconButton size="small" disabled={!hasNextPage} onClick={() => onPageChange(page + 1)}>
          <ChevronRightIcon />
        </IconButton>
      </Box>
    </Box>
  );
}
