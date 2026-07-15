import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
} from '@mui/material';
import { LoadingState } from '../LoadingState';
import { ErrorState } from '../ErrorState';
import { Pager } from './Pager';
import type { ColumnDef, DataTableProps } from './DataTable.types';

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  loading,
  error,
  emptyMessage = 'No results.',
  onRowClick,
  sortBy,
  order,
  onSortChange,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
  hasNextPage,
}: DataTableProps<T>) {
  if (loading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;

  function handleSort(column: ColumnDef<T>) {
    const key = column.sortKey ?? column.id;
    if (sortBy === key) {
      onSortChange(key, order === 'asc' ? 'desc' : 'asc');
    } else {
      onSortChange(key, 'asc');
    }
  }

  return (
    <Paper>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              {columns.map((column) => {
                const key = column.sortKey ?? column.id;
                return (
                  <TableCell key={column.id} align={column.align} sx={{ width: column.width }}>
                    {column.sortable ? (
                      <TableSortLabel
                        active={sortBy === key}
                        direction={sortBy === key ? order : 'asc'}
                        onClick={() => handleSort(column)}
                      >
                        {column.label}
                      </TableSortLabel>
                    ) : (
                      column.label
                    )}
                  </TableCell>
                );
              })}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={columns.length}>{emptyMessage}</TableCell>
              </TableRow>
            )}
            {rows.map((row) => (
              <TableRow
                key={rowKey(row)}
                hover={Boolean(onRowClick)}
                onClick={() => onRowClick?.(row)}
                sx={{ cursor: onRowClick ? 'pointer' : 'default' }}
              >
                {columns.map((column) => (
                  <TableCell key={column.id} align={column.align}>
                    {column.render
                      ? column.render(row)
                      : String((row as Record<string, unknown>)[column.id] ?? '')}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Pager
        page={page}
        pageSize={pageSize}
        hasNextPage={hasNextPage}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />
    </Paper>
  );
}
