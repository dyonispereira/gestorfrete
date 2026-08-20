import { apiFetch } from "@/shared/lib/api-client";
import type { CreateVehicleCompositionRequest, PaginatedResponse, VehicleComposition } from "@gestorfrete/types";

export interface ListVehicleCompositionsParams {
  page?: number;
  limit?: number;
  veiculo_tracionador_id?: string;
  tipo_combinacao?: string;
  vigente?: boolean;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | boolean | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

/** No update/delete service function — D248, "editing" is `createVehicleComposition` again. */
export function listVehicleCompositions(params: ListVehicleCompositionsParams = {}): Promise<PaginatedResponse<VehicleComposition>> {
  return apiFetch<PaginatedResponse<VehicleComposition>>(`/vehicle-compositions${toQuery(params)}`);
}

export function createVehicleComposition(body: CreateVehicleCompositionRequest): Promise<VehicleComposition> {
  return apiFetch<VehicleComposition>("/vehicle-compositions", { method: "POST", body });
}
