import { apiFetch } from "@/shared/lib/api-client";
import type { CreateOccurrenceRequest, Occurrence, PaginatedResponse, UpdateOccurrenceRequest } from "@gestorfrete/types";

export interface ListOccurrencesParams {
  page?: number;
  limit?: number;
  type?: string;
  status?: string;
  severity?: string;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listOccurrences(tripId: string, params: ListOccurrencesParams = {}): Promise<PaginatedResponse<Occurrence>> {
  return apiFetch<PaginatedResponse<Occurrence>>(`/viagens/${tripId}/occurrences${toQuery(params)}`);
}

export function getOccurrence(tripId: string, occurrenceId: string): Promise<Occurrence> {
  return apiFetch<Occurrence>(`/viagens/${tripId}/occurrences/${occurrenceId}`);
}

export function createOccurrence(tripId: string, body: CreateOccurrenceRequest): Promise<Occurrence> {
  return apiFetch<Occurrence>(`/viagens/${tripId}/occurrences`, { method: "POST", body });
}

/** No DELETE — a wrong Ocorrência is corrected via `status: RESOLVIDA`, never removed. */
export function updateOccurrence(tripId: string, occurrenceId: string, body: UpdateOccurrenceRequest): Promise<Occurrence> {
  return apiFetch<Occurrence>(`/viagens/${tripId}/occurrences/${occurrenceId}`, { method: "PATCH", body });
}
