// Hand-maintained against backend/app/models/control_review.py - no
// response_model on these routes, so it's a raw ORM row.
export interface ControlReview {
  id: number;
  control_id: number;
  reviewer: string | null;
  previous_status: string | null;
  new_status: string;
  notes: string | null;
  org_id: number;
  reviewed_at: string; // ISO 8601
}

// POST /controls/{id}/review body (backend/app/schemas/
// control_review.py - ControlReviewCreate).
export interface ControlReviewCreateInput {
  new_status: string;
  notes?: string | null;
}
