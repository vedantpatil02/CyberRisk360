import { apiClient } from '../client';
import type { Role } from '../types/auth';
import type { Organization, OrganizationCreateInput } from '../types/organization';

// GET/POST /organizations both use require_role(ROLE_SUPER_ADMIN) -
// platform super-admin only, not just ROLE_ADMIN (org provisioning is
// a cross-tenant, platform-level action).
export const ORGANIZATION_MANAGEMENT_ROLES: readonly Role[] = ['super_admin'];

export async function listOrganizations(): Promise<Organization[]> {
  const { data } = await apiClient.get<Organization[]>('/organizations');
  return data;
}

export async function createOrganization(
  input: OrganizationCreateInput,
): Promise<Organization> {
  const { data } = await apiClient.post<Organization>('/organizations', input);
  return data;
}
