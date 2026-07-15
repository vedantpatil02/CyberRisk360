export type SortOrder = 'asc' | 'desc';

export interface ListQueryParams {
  limit?: number;
  offset?: number;
  sort_by?: string;
  order?: SortOrder;
}
