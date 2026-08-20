import { apiFetch } from "@/shared/lib/api-client";
import type { CreateRoleRequest, PaginatedResponse, Role, UpdateRoleRequest } from "@gestorfrete/types";

export interface ListRolesParams {
  page?: number;
  limit?: number;
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

export function listRoles(params: ListRolesParams = {}): Promise<PaginatedResponse<Role>> {
  return apiFetch<PaginatedResponse<Role>>(`/roles${toQuery(params)}`);
}

export function getRole(id: string): Promise<Role> {
  return apiFetch<Role>(`/roles/${id}`);
}

export function createRole(body: CreateRoleRequest): Promise<Role> {
  return apiFetch<Role>("/roles", { method: "POST", body });
}

export function updateRole(id: string, body: UpdateRoleRequest): Promise<Role> {
  return apiFetch<Role>(`/roles/${id}`, { method: "PATCH", body });
}

export function deleteRole(id: string): Promise<void> {
  return apiFetch<void>(`/roles/${id}`, { method: "DELETE" });
}
