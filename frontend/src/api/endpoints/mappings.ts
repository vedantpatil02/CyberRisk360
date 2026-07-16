import { apiClient } from '../client';
import type { Role } from '../types/auth';
import type { Mapping, MappingHistoryEntry } from '../types/mapping';

// GET /mappings/pending, GET .../mappings, GET .../history all use
// admin/analyst/auditor; approve/reject narrow to admin/analyst only
// (matches backend/app/api/mappings.py exactly).
export const MAPPING_READ_ROLES: readonly Role[] = ['admin', 'analyst', 'auditor'];
export const MAPPING_REVIEW_ROLES: readonly Role[] = ['admin', 'analyst'];

export async function listPendingMappings(): Promise<Mapping[]> {
  const { data } = await apiClient.get<Mapping[]>('/mappings/pending');
  return data;
}

export async function getMappingHistory(mappingId: number): Promise<MappingHistoryEntry[]> {
  const { data } = await apiClient.get<MappingHistoryEntry[]>(`/mappings/${mappingId}/history`);
  return data;
}

export async function approveMapping(mappingId: number, note?: string): Promise<Mapping> {
  const { data } = await apiClient.patch<Mapping>(`/mappings/${mappingId}/approve`, { note });
  return data;
}

export async function rejectMapping(mappingId: number, note?: string): Promise<Mapping> {
  const { data } = await apiClient.patch<Mapping>(`/mappings/${mappingId}/reject`, { note });
  return data;
}
