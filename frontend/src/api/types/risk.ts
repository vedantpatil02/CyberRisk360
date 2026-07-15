// Hand-maintained against backend/app/models/risk.py - the API has no
// response_model for this resource, so it serializes every raw ORM
// column, no relationship data (asset_id, not the linked asset's
// fields).
export type RiskLevel = 'Critical' | 'High' | 'Medium' | 'Low';
export type RiskStatus = 'Open' | 'Under Review' | 'Mitigated' | 'Accepted' | 'Closed';
export type RiskSource = 'manual' | 'auto';

export interface Risk {
  id: number;
  title: string;
  description: string;
  asset_id: number | null;
  impact: number; // 1-5
  likelihood: number; // 1-5
  risk_score: number | null;
  risk_level: RiskLevel | null;
  owner: string | null;
  status: RiskStatus;
  source: RiskSource;
  org_id: number;
  assignee_id: number | null;
  due_date: string | null; // ISO 8601
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}

export interface RiskListParams {
  limit?: number;
  offset?: number;
  sort_by?: 'id' | 'risk_score' | 'risk_level' | 'status' | 'due_date' | 'assignee_id';
  order?: 'asc' | 'desc';
  risk_level?: RiskLevel;
  status?: RiskStatus;
  source?: RiskSource;
  asset_id?: number;
  assignee_id?: number;
  sla_breached?: boolean;
}
