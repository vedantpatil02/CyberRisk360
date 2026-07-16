import { apiClient } from '../client';
import type { Role } from '../types/auth';
import type { ControlReview, ControlReviewCreateInput } from '../types/control_review';

// POST /controls/{id}/review requires COMPLIANCE_ROLES on the backend
// - an exact match for that group's own documented purpose ("may
// manage controls/compliance state").
export const CONTROL_REVIEW_ROLES: readonly Role[] = ['admin', 'analyst', 'grc_analyst'];

export async function submitControlReview(
  controlId: number,
  input: ControlReviewCreateInput,
): Promise<ControlReview> {
  const { data } = await apiClient.post<ControlReview>(`/controls/${controlId}/review`, input);
  return data;
}

export async function getControlReviews(controlId: number): Promise<ControlReview[]> {
  const { data } = await apiClient.get<ControlReview[]>(`/controls/${controlId}/reviews`);
  return data;
}
