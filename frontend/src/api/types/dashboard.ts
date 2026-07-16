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

// GET /dashboard/grc/{framework_name} - matches
// backend/app/analytics/grc.py::get_grc_dashboard exactly.
export interface RiskyControl {
  control_id: string;
  name: string;
  affected_vulnerabilities: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  risk_score: number;
}

export interface GrcDashboard {
  framework: string;
  compliance_score: number;
  total_controls: number;
  implemented_controls: number;
  partial_controls: number;
  missing_controls: number;
  overall_risk_score: number;
  top_risky_controls: RiskyControl[];
  gap_summary: {
    affected_controls: number;
    unaffected_controls: number;
  };
}

// GET /dashboard/executive - matches
// backend/app/analytics/executive.py::get_executive_dashboard exactly.
export interface RiskyAsset {
  asset: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
  risk_score: number;
  total_vulnerabilities: number;
}

export interface ExecutiveDashboard {
  assets: {
    total: number;
    highest_risk_asset: RiskyAsset | null;
  };
  vulnerabilities: {
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  controls: {
    total: number;
  };
  risk: {
    overall_control_risk_score: number;
    top_risky_control: RiskyControl | null;
  };
}
