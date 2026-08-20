import { apiFetch } from "@/shared/lib/api-client";
import type { PaginatedResponse, Permission } from "@gestorfrete/types";

export interface ListPermissionsParams {
  page?: number;
  limit?: number;
  module?: string;
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

export function listPermissions(params: ListPermissionsParams = {}): Promise<PaginatedResponse<Permission>> {
  return apiFetch<PaginatedResponse<Permission>>(`/permissions${toQuery(params)}`);
}
