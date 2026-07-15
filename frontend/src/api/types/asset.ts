// Hand-maintained against backend/app/models/asset.py.
export interface Asset {
  id: number;
  name: string;
  asset_type: string;
  owner: string;
  criticality: string;
  ip_address: string | null;
  environment: string;
  org_id: number;
}

// GET /assets/{id}/vulnerabilities - a purpose-built dict from
// app/api/assets.py, not the full Vulnerability model.
export interface AssetVulnerabilitySummary {
  id: number;
  plugin_id: string | null;
  title: string;
  severity: string;
  cvss_score: number;
  status: string;
}

// GET /assets/{id}/summary
export interface AssetSummary {
  asset_id: number;
  asset_name: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
  total: number;
}

export interface AssetListParams {
  limit?: number;
  offset?: number;
  sort_by?: 'id' | 'name' | 'criticality' | 'environment';
  order?: 'asc' | 'desc';
  criticality?: string;
  environment?: string;
  asset_type?: string;
}
