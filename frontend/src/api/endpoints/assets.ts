import { apiClient } from '../client';
import type { Role } from '../types/auth';
import type {
  Asset,
  AssetListParams,
  AssetSummary,
  AssetVulnerabilitySummary,
} from '../types/asset';

// GET /assets has no role check at all (any authenticated user) -
// unlike its own detail endpoints below, which require this tuple.
// Two different role gates on the same resource, both taken directly
// from backend/app/api/assets.py rather than assumed uniform.
export const ASSET_DETAIL_READ_ROLES: readonly Role[] = ['admin', 'analyst', 'auditor'];

export async function listAssets(params: AssetListParams): Promise<Asset[]> {
  const { data } = await apiClient.get<Asset[]>('/assets', { params });
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
