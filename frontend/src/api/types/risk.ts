// Hand-maintained against backend/app/models/risk.py - the API has no
// response_model for this resource, so it serializes every raw ORM
// column, no relationship data (asset_id, not the linked asset's
// fields).
export type RiskLevel = 'Critical' | 'High' | 'Medium' | 'Low';
export type RiskStatus =
  | 'Open'
  | 'Under Review'
  | 'Mitigated'
  | 'Accepted'
  | 'Transferred'
  | 'Avoided'
  | 'Closed';
export type RiskSource = 'manual' | 'auto';

// Risk Treatment Workflow (backend/app/services/risks/risk_treatment.py)
export type TreatmentType = 'mitigate' | 'accept' | 'transfer' | 'avoid';
export type ApprovalStatus = 'pending' | 'approved' | 'rejected';

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
  treatment_type: TreatmentType | null;
  treatment_justification: string | null;
  approval_status: ApprovalStatus | null;
  approved_by: string | null;
  approved_at: string | null; // ISO 8601
}

// GET /risks/{id}/treatment/history
export interface RiskTreatmentHistoryEntry {
  id: number;
  risk_id: number;
  action: 'proposed' | 'approved' | 'rejected';
  previous_status: RiskStatus | null;
  new_status: RiskStatus;
  treatment_type: TreatmentType | null;
  actor: string | null;
  note: string | null;
  created_at: string; // ISO 8601
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

// POST /risks body (backend/app/schemas/risk.py - RiskCreate). No
// status/risk_score/risk_level/source - all server-computed/defaulted.
export interface RiskCreateInput {
  title: string;
  description: string;
  asset_id: number;
  impact: number; // 1-5
  likelihood: number; // 1-5
  owner: string;
  assignee_id?: number | null;
  due_date?: string | null;
}

// PUT /risks/{id} body (RiskUpdate) - all optional.
export interface RiskUpdateInput {
  title?: string;
  description?: string;
  impact?: number;
  likelihood?: number;
  owner?: string;
  status?: RiskStatus;
  assignee_id?: number | null;
  due_date?: string | null;
}
