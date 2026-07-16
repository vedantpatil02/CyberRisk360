// Hand-maintained against backend/app/models/framework.py - no
// response_model on GET /frameworks, so it's a raw ORM row (no
// nested categories/controls - see FrameworkGaps below for how a
// framework's controls are actually reached).
export interface Framework {
  id: number;
  name: string;
  short_name: string;
  version: string;
  publisher: string;
  description: string | null;
  release_year: number | null;
}

// GET /frameworks/{name}/summary - deliberately NOT the same number
// as /compliance-summary's compliance_score (see that endpoint's own
// docstring in app/api/controls.py): this measures the % of controls
// with an approved vulnerability mapping, not manually-marked
// implementation status.
export interface FrameworkSummary {
  framework: string;
  total_controls: number;
  affected_controls: number;
  affected_vulnerabilities: number;
  vulnerability_coverage_score: number;
}

// GET /frameworks/{name}/gaps - the only endpoint that lists a
// framework's controls; there is no GET /categories and GET
// /controls is unfiltered/unpaginated (all 465 controls across every
// framework), so gaps is the practical way to browse one framework's
// controls, grouped by whether they have vulnerability coverage.
export interface FrameworkGapControl {
  id: number; // Control's numeric id - needed for POST /controls/{id}/review
  control_id: string;
  name: string;
  status: string; // Missing / Partially Implemented / Implemented
  affected_vulnerabilities: number;
}

export interface FrameworkGaps {
  framework: string;
  total_controls: number;
  affected_controls: FrameworkGapControl[];
  unaffected_controls: FrameworkGapControl[];
}

// POST /frameworks body (backend/app/schemas/framework.py -
// FrameworkCreate).
export interface FrameworkCreateInput {
  name: string;
  short_name: string;
  version: string;
  publisher: string;
  description?: string | null;
  release_year?: number | null;
}

// PATCH /frameworks/{id} body (FrameworkUpdate) - all optional.
// short_name is deliberately not included - it isn't updatable on the
// backend once a framework is created.
export interface FrameworkUpdateInput {
  name?: string;
  version?: string;
  publisher?: string;
  description?: string | null;
  release_year?: number | null;
}
