import { apiFetch } from "@/shared/lib/api-client";
import type {
  CreateVehicleCategoryRequest,
  PaginatedResponse,
  UpdateVehicleCategoryRequest,
  VehicleCategory,
} from "@gestorfrete/types";

export interface ListVehicleCategoriesParams {
  page?: number;
  limit?: number;
  status?: string;
  search?: string;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listVehicleCategories(
  params: ListVehicleCategoriesParams = {}
): Promise<PaginatedResponse<VehicleCategory>> {
  return apiFetch<PaginatedResponse<VehicleCategory>>(`/categorias-veiculo${toQuery(params)}`);
}

export function createVehicleCategory(body: CreateVehicleCategoryRequest): Promise<VehicleCategory> {
  return apiFetch<VehicleCategory>("/categorias-veiculo", { method: "POST", body });
}

/** Sem DELETE — desativação é `status: "INATIVA"` através deste mesmo PATCH. */
export function updateVehicleCategory(id: string, body: UpdateVehicleCategoryRequest): Promise<VehicleCategory> {
  return apiFetch<VehicleCategory>(`/categorias-veiculo/${id}`, { method: "PATCH", body });
}
