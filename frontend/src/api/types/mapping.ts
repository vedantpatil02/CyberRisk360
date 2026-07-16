// GET /mappings/pending, GET /vulnerabilities/{id}/mappings - matches
// backend/app/models/vulnerability_control_mapping.py's raw columns
// exactly (no response_model on these routes, so every column
// serializes as-is; no resolved control/vulnerability name - only IDs).
export interface Mapping {
  id: number;
  vulnerability_id: number;
  control_id: number;
  match_type: string | null;
  matched_value: string | null;
  confidence_score: number | null;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
  org_id: number;
}

// GET /mappings/{id}/history - matches
// backend/app/models/mapping_history.py's raw columns exactly.
export interface MappingHistoryEntry {
  id: number;
  mapping_id: number;
  action: string;
  previous_status: string | null;
  new_status: string;
  actor: string | null;
  note: string | null;
  created_at: string;
  org_id: number;
}
