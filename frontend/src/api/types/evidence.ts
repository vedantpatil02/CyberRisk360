// GET .../evidence, POST .../evidence - matches
// backend/app/services/remediation/evidence.py::serialize_evidence
// exactly. `stored_path` is deliberately never serialized by the
// backend (server-internal detail; downloads go through
// GET /evidence/{id}/download by id).
export interface EvidenceAttachment {
  id: number;
  vulnerability_id: number | null;
  risk_id: number | null;
  file_name: string;
  content_type: string | null;
  file_size: number;
  uploaded_by_id: number;
  org_id: number;
  uploaded_at: string; // ISO 8601
  expires_at: string | null; // ISO 8601
}
