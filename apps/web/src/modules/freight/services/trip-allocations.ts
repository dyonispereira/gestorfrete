import { apiFetch } from "@/shared/lib/api-client";
import type {
  CreateTripAllocationRequest,
  PaginatedResponse,
  ReallocateTripResourcesRequest,
  TripAllocation,
} from "@gestorfrete/types";

/** `?history=false` (default): bare current allocation. `?history=true`: full paginated history. */
export function getCurrentTripAllocation(tripId: string): Promise<TripAllocation> {
  return apiFetch<TripAllocation>(`/viagens/${tripId}/resources`);
}

export function getTripAllocationHistory(tripId: string): Promise<PaginatedResponse<TripAllocation>> {
  return apiFetch<PaginatedResponse<TripAllocation>>(`/viagens/${tripId}/resources?history=true`);
}

/** Only works once — 409 `FREIGHT_TRIP_ALREADY_HAS_ALLOCATION` if a VIGENTE row already exists. */
export function createTripAllocation(tripId: string, body: CreateTripAllocationRequest): Promise<TripAllocation> {
  return apiFetch<TripAllocation>(`/viagens/${tripId}/resources`, { method: "POST", body });
}

/** Supersedes the current row (old → SUBSTITUIDA, new inserted) — never PATCH/DELETE. */
export function reallocateTripResources(
  tripId: string,
  body: ReallocateTripResourcesRequest
): Promise<TripAllocation> {
  return apiFetch<TripAllocation>(`/viagens/${tripId}/commands/reallocate-resources`, { method: "POST", body });
}
