import { useCallback, useState } from 'react';
import type { SortOrder } from '../api/types/pagination';

interface UsePaginatedListStateOptions<F extends object> {
  defaultSortBy: string;
  defaultOrder?: SortOrder;
  defaultPageSize?: number;
  defaultFilters?: F;
}

// Generic page/sort/filter UI-state manager shared by every resource
// list page. Not resource-specific - Risks/Assets reuse this
// unchanged once they're added.
export function usePaginatedListState<F extends object>({
  defaultSortBy,
  defaultOrder = 'asc',
  defaultPageSize = 25,
  defaultFilters,
}: UsePaginatedListStateOptions<F>) {
  const [page, setPageState] = useState(0);
  const [pageSize, setPageSizeState] = useState(defaultPageSize);
  const [sortBy, setSortByState] = useState(defaultSortBy);
  const [order, setOrderState] = useState<SortOrder>(defaultOrder);
  const [filters, setFiltersState] = useState<F>(defaultFilters ?? ({} as F));

  const setPage = useCallback((next: number) => setPageState(next), []);

  const setPageSize = useCallback((size: number) => {
    setPageSizeState(size);
    setPageState(0);
  }, []);

  const setSort = useCallback((nextSortBy: string, nextOrder: SortOrder) => {
    setSortByState(nextSortBy);
    setOrderState(nextOrder);
    setPageState(0);
  }, []);

  const setFilters = useCallback((next: F) => {
    setFiltersState(next);
    setPageState(0);
  }, []);

  return {
    page,
    pageSize,
    sortBy,
    order,
    filters,
    offset: page * pageSize,
    // +1 over the page size: if the response comes back with pageSize+1
    // rows, there's a next page (see DataTable.types.ts's hasNextPage) -
    // the API never returns a total count to derive this from otherwise.
    limit: pageSize + 1,
    setPage,
    setPageSize,
    setSort,
    setFilters,
  };
}
