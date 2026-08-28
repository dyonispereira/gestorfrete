import { apiFetch } from "@/shared/lib/api-client";
import type { CancelMdfeRequest, CreateMdfeRequest, Mdfe, PaginatedResponse, XmlReference } from "@gestorfrete/types";

export interface ListMdfesParams {
  page?: number;
  limit?: number;
  trip_id?: string;
  status?: string;
  series?: string;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listMdfes(params: ListMdfesParams = {}): Promise<PaginatedResponse<Mdfe>> {
  return apiFetch<PaginatedResponse<Mdfe>>(`/mdfes${toQuery(params)}`);
}

export function getMdfe(id: string): Promise<Mdfe> {
  return apiFetch<Mdfe>(`/mdfes/${id}`);
}

/** O único tipo de documento com criação real pelo usuário — exige todo `cte_id` AUTORIZADO e da mesma viagem. */
export function createMdfe(body: CreateMdfeRequest): Promise<Mdfe> {
  return apiFetch<Mdfe>("/mdfes", { method: "POST", body });
}

export function closeMdfe(id: string): Promise<Mdfe> {
  return apiFetch<Mdfe>(`/mdfes/${id}/commands/close`, { method: "POST" });
}

export function cancelMdfe(id: string, body: CancelMdfeRequest): Promise<Mdfe> {
  return apiFetch<Mdfe>(`/mdfes/${id}/commands/cancel`, { method: "POST", body });
}

export function getMdfeXml(id: string): Promise<XmlReference> {
  return apiFetch<XmlReference>(`/mdfes/${id}/xml`);
}
