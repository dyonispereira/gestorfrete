import { apiFetch } from "@/shared/lib/api-client";
import type { CancelCteRequest, Cte, PaginatedResponse, XmlReference } from "@gestorfrete/types";

export interface ListCtesParams {
  page?: number;
  limit?: number;
  trip_id?: string;
  status?: string;
  series?: string;
  access_key?: string;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listCtes(params: ListCtesParams = {}): Promise<PaginatedResponse<Cte>> {
  return apiFetch<PaginatedResponse<Cte>>(`/ctes${toQuery(params)}`);
}

export function getCte(id: string): Promise<Cte> {
  return apiFetch<Cte>(`/ctes/${id}`);
}

/** Sem `createCte` — nunca há `POST /ctes` (D396); só existe via despacho de Viagem. */

export function validateCte(id: string): Promise<Cte> {
  return apiFetch<Cte>(`/ctes/${id}/commands/validate`, { method: "POST" });
}

export function signCte(id: string): Promise<Cte> {
  return apiFetch<Cte>(`/ctes/${id}/commands/sign`, { method: "POST" });
}

export function transmitCte(id: string): Promise<Cte> {
  return apiFetch<Cte>(`/ctes/${id}/commands/transmit`, { method: "POST" });
}

export function inutilizeCte(id: string): Promise<Cte> {
  return apiFetch<Cte>(`/ctes/${id}/commands/inutilize`, { method: "POST" });
}

export function cancelCte(id: string, body: CancelCteRequest): Promise<Cte> {
  return apiFetch<Cte>(`/ctes/${id}/commands/cancel`, { method: "POST", body });
}

/** 404 `FISCAL_CTE_XML_NOT_AVAILABLE` antes de AUTORIZADO — nunca alcançável nesta base, hoje. */
export function getCteXml(id: string): Promise<XmlReference> {
  return apiFetch<XmlReference>(`/ctes/${id}/xml`);
}
