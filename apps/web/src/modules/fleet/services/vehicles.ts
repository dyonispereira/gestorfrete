import { apiFetch } from "@/shared/lib/api-client";
import type { CreateVehicleRequest, PaginatedResponse, UpdateVehicleRequest, Vehicle } from "@gestorfrete/types";

export interface ListVehiclesParams {
  page?: number;
  limit?: number;
  search?: string;
  placa?: string;
  status?: string;
  categoria_id?: string;
  fabricante?: string;
  modelo?: string;
  ano?: number;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listVehicles(params: ListVehiclesParams = {}): Promise<PaginatedResponse<Vehicle>> {
  return apiFetch<PaginatedResponse<Vehicle>>(`/veiculos${toQuery(params)}`);
}

export function getVehicle(id: string): Promise<Vehicle> {
  return apiFetch<Vehicle>(`/veiculos/${id}`);
}

export function createVehicle(body: CreateVehicleRequest): Promise<Vehicle> {
  return apiFetch<Vehicle>("/veiculos", { method: "POST", body });
}

export function updateVehicle(id: string, body: UpdateVehicleRequest): Promise<Vehicle> {
  return apiFetch<Vehicle>(`/veiculos/${id}`, { method: "PATCH", body });
}

export function deleteVehicle(id: string): Promise<void> {
  return apiFetch<void>(`/veiculos/${id}`, { method: "DELETE" });
}
