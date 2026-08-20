import { apiFetch } from "@/shared/lib/api-client";
import type { Client, CreateClientRequest, PaginatedResponse, UpdateClientRequest } from "@gestorfrete/types";

export interface ListClientsParams {
  page?: number;
  limit?: number;
  status?: string;
  document?: string;
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

export function listClients(params: ListClientsParams = {}): Promise<PaginatedResponse<Client>> {
  return apiFetch<PaginatedResponse<Client>>(`/clients${toQuery(params)}`);
}

export function getClient(id: string): Promise<Client> {
  return apiFetch<Client>(`/clients/${id}`);
}

export function createClient(body: CreateClientRequest): Promise<Client> {
  return apiFetch<Client>("/clients", { method: "POST", body });
}

export function updateClient(id: string, body: UpdateClientRequest): Promise<Client> {
  return apiFetch<Client>(`/clients/${id}`, { method: "PATCH", body });
}

export function deactivateClient(id: string): Promise<void> {
  return apiFetch<void>(`/clients/${id}`, { method: "DELETE" });
}
