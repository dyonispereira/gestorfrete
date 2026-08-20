import { apiFetch } from "@/shared/lib/api-client";
import type { PaginatedResponse, VehicleAvailability } from "@gestorfrete/types";

export interface ListVehicleAvailabilityParams {
  page?: number;
  limit?: number;
  status?: string;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

/** Pure read model — no write function exists anywhere, matching the Backend having no write endpoint. */
export function listVehicleAvailability(params: ListVehicleAvailabilityParams = {}): Promise<PaginatedResponse<VehicleAvailability>> {
  return apiFetch<PaginatedResponse<VehicleAvailability>>(`/veiculos/disponibilidade${toQuery(params)}`);
}

export function getVehicleAvailability(vehicleId: string): Promise<VehicleAvailability> {
  return apiFetch<VehicleAvailability>(`/veiculos/${vehicleId}/disponibilidade`);
}
