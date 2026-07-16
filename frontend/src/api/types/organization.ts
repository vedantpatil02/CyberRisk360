// GET/POST /organizations - matches
// backend/app/schemas/organization.py exactly.
export interface Organization {
  id: number;
  name: string;
  slug: string;
  created_at: string | null; // ISO 8601
}

export interface OrganizationCreateInput {
  name: string;
  slug: string;
}
