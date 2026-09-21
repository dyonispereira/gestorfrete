import { apiFetch } from "@/shared/lib/api-client";
import type { CreateInvoiceRequest, EligibleTrip, Invoice, PaginatedResponse } from "@gestorfrete/types";

export interface ListInvoicesParams {
  page?: number;
  limit?: number;
  client_id?: string;
  status?: string;
  trip_id?: string;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listInvoices(params: ListInvoicesParams = {}): Promise<PaginatedResponse<Invoice>> {
  return apiFetch<PaginatedResponse<Invoice>>(`/faturas${toQuery(params)}`);
}

export function getInvoice(id: string): Promise<Invoice> {
  return apiFetch<Invoice>(`/faturas/${id}`);
}

/** Lote Financeiro, Parte 3 — "a seleção deve mostrar somente viagens faturáveis conforme as
 * regras já existentes" (pedido explícito do usuário). */
export function listEligibleTrips(clientId: string): Promise<EligibleTrip[]> {
  return apiFetch<EligibleTrip[]>(`/faturas/viagens-elegiveis?client_id=${clientId}`);
}

export function createInvoice(body: CreateInvoiceRequest): Promise<Invoice> {
  return apiFetch<Invoice>("/faturas", { method: "POST", body });
}

export function cancelInvoice(id: string): Promise<Invoice> {
  return apiFetch<Invoice>(`/faturas/${id}/commands/cancel`, { method: "POST" });
}
