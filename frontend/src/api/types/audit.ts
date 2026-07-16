// Hand-maintained against backend/app/models/audit.py and
// audit_finding.py - no response_model on these routes, so they
// serialize every raw ORM column.
export type AuditStatus = 'Planned' | 'In Progress' | 'Completed' | 'Closed';
export type AuditFindingSeverity = 'Critical' | 'High' | 'Medium' | 'Low';
export type AuditFindingStatus = 'Open' | 'Remediated' | 'Accepted' | 'Closed';

export interface Audit {
  id: number;
  title: string;
  framework_id: number | null;
  lead_auditor_id: number | null;
  scope: string | null;
  status: AuditStatus;
  start_date: string | null; // ISO 8601
  end_date: string | null; // ISO 8601
  org_id: number;
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601
}

export interface AuditFinding {
  id: number;
  audit_id: number;
  control_id: number | null;
  title: string;
  description: string | null;
  severity: AuditFindingSeverity;
  status: AuditFindingStatus;
  created_at: string; // ISO 8601
}

export interface AuditListParams {
  limit?: number;
  offset?: number;
  sort_by?: 'id' | 'title' | 'status' | 'start_date' | 'end_date';
  order?: 'asc' | 'desc';
  status?: AuditStatus;
  framework_id?: number;
}

// POST /audits body (backend/app/schemas/audit_engagement.py -
// AuditCreate).
export interface AuditCreateInput {
  title: string;
  framework_id?: number | null;
  lead_auditor_id?: number | null;
  scope?: string | null;
  start_date?: string | null;
  end_date?: string | null;
}

// PUT /audits/{id} body (AuditUpdate) - all optional.
export interface AuditUpdateInput {
  title?: string;
  framework_id?: number | null;
  lead_auditor_id?: number | null;
  scope?: string | null;
  status?: AuditStatus;
  start_date?: string | null;
  end_date?: string | null;
}

// POST /audits/{id}/findings body (AuditFindingCreate).
export interface AuditFindingCreateInput {
  title: string;
  description?: string | null;
  control_id?: number | null;
  severity: AuditFindingSeverity;
}

// PUT /findings/{id} body (AuditFindingUpdate) - all optional.
export interface AuditFindingUpdateInput {
  title?: string;
  description?: string | null;
  severity?: AuditFindingSeverity;
  status?: AuditFindingStatus;
}
