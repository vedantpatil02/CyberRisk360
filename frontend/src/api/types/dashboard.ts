// Matches GET /dashboard/overview's response shape exactly -
// backend/app/api/dashboard.py::dashboard_overview.
export interface TopAsset {
  asset_id: number;
  asset_name: string;
  vulnerability_count: number;
}

export interface DashboardOverview {
  total_assets: number;
  total_vulnerabilities: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  open: number;
  closed: number;
  top_assets: TopAsset[];
}
