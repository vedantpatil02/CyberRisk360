import { apiClient } from '../client';
import type { Role } from '../types/auth';
import type {
  Asset,
  AssetCreateInput,
  AssetListParams,
  AssetSummary,
  AssetUpdateInput,
  AssetVulnerabilitySummary,
} from '../types/asset';

// GET /assets has no role check at all (any authenticated user) -
// unlike its own detail endpoints below, which require this tuple.
// Two different role gates on the same resource, both taken directly
// from backend/app/api/assets.py rather than assumed uniform.
export const ASSET_DETAIL_READ_ROLES: readonly Role[] = ['admin', 'analyst', 'auditor'];

// POST/PUT /assets both require this pair on the backend.
export const ASSET_WRITE_ROLES: readonly Role[] = ['admin', 'analyst'];

export async function listAssets(params: AssetListParams): Promise<Asset[]> {
  const { data } = await apiClient.get<Asset[]>('/assets', { params });
  return data;
}

export async function getAsset(id: number): Promise<Asset> {
  const { data } = await apiClient.get<Asset>(`/assets/${id}`);
  return data;
}

export async function getAssetSummary(id: number): Promise<AssetSummary> {
  const { data } = await apiClient.get<AssetSummary>(`/assets/${id}/summary`);
  return data;
}

export async function getAssetVulnerabilities(id: number): Promise<AssetVulnerabilitySummary[]> {
  const { data } = await apiClient.get<AssetVulnerabilitySummary[]>(
    `/assets/${id}/vulnerabilities`,
  );
  return data;
}

// Returns {message} only - the backend doesn't return the created
// record itself.
export async function createAsset(input: AssetCreateInput): Promise<{ message: string }> {
  const { data } = await apiClient.post<{ message: string }>('/assets', input);
  return data;
}

// Returns the full updated Asset - unlike Risks/Vulnerabilities'
// PUT (which only returns {message}), this endpoint was built to
// return the record directly so the frontend doesn't need a second
// round trip after editing.
export async function updateAsset(id: number, input: AssetUpdateInput): Promise<Asset> {
  const { data } = await apiClient.put<Asset>(`/assets/${id}`, input);
  return data;
}
