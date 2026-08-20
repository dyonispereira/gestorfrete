import { apiFetch } from "@/shared/lib/api-client";
import type { CreateImplementRequest, Implement, PaginatedResponse, UpdateImplementRequest } from "@gestorfrete/types";

export interface ListImplementsParams {
  page?: number;
  limit?: number;
  search?: string;
  tipo_carroceria?: string;
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

export function listImplements(params: ListImplementsParams = {}): Promise<PaginatedResponse<Implement>> {
  return apiFetch<PaginatedResponse<Implement>>(`/implementos${toQuery(params)}`);
}

export function getImplement(id: string): Promise<Implement> {
  return apiFetch<Implement>(`/implementos/${id}`);
}

export function createImplement(body: CreateImplementRequest): Promise<Implement> {
  return apiFetch<Implement>("/implementos", { method: "POST", body });
}

export function updateImplement(id: string, body: UpdateImplementRequest): Promise<Implement> {
  return apiFetch<Implement>(`/implementos/${id}`, { method: "PATCH", body });
}

export function deleteImplement(id: string): Promise<void> {
  return apiFetch<void>(`/implementos/${id}`, { method: "DELETE" });
}
