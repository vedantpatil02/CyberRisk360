import type { ReactNode } from 'react';
import type { SortOrder } from '../../api/types/pagination';

export interface ColumnDef<T> {
  id: string;
  label: string;
  sortable?: boolean;
  // Overrides the API's sort_by name when it differs from `id`.
  sortKey?: string;
  align?: 'left' | 'right' | 'center';
  width?: string | number;
  render?: (row: T) => ReactNode;
}

export interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  loading?: boolean;
  error?: unknown;
  emptyMessage?: string;
  onRowClick?: (row: T) => void;

  sortBy: string;
  order: SortOrder;
  onSortChange: (sortBy: string, order: SortOrder) => void;

  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  // Backend list endpoints never return a total count - the caller
  // derives this from the limit+1 trick (see usePaginatedListState)
  // rather than DataTable ever assuming a known row count.
  hasNextPage: boolean;
}
