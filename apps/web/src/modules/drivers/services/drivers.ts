import { apiFetch } from "@/shared/lib/api-client";
import type { CreateDriverRequest, Driver, PaginatedResponse, UpdateDriverRequest } from "@gestorfrete/types";

export interface ListDriversParams {
  page?: number;
  limit?: number;
  status?: string;
  employment_type?: string;
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

export function listDrivers(params: ListDriversParams = {}): Promise<PaginatedResponse<Driver>> {
  return apiFetch<PaginatedResponse<Driver>>(`/drivers${toQuery(params)}`);
}

export function getDriver(id: string): Promise<Driver> {
  return apiFetch<Driver>(`/drivers/${id}`);
}

export function createDriver(body: CreateDriverRequest): Promise<Driver> {
  return apiFetch<Driver>("/drivers", { method: "POST", body });
}

export function updateDriver(id: string, body: UpdateDriverRequest): Promise<Driver> {
  return apiFetch<Driver>(`/drivers/${id}`, { method: "PATCH", body });
}

export function deleteDriver(id: string): Promise<void> {
  return apiFetch<void>(`/drivers/${id}`, { method: "DELETE" });
}

/** Named commands, not a generic status PATCH — `fitness_status` is otherwise read-only. Both return the updated Driver. */
export function blockDriver(id: string): Promise<Driver> {
  return apiFetch<Driver>(`/drivers/${id}/block`, { method: "POST" });
}

export function unblockDriver(id: string): Promise<Driver> {
  return apiFetch<Driver>(`/drivers/${id}/unblock`, { method: "POST" });
}
