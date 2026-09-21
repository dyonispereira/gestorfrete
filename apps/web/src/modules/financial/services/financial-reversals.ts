import { apiFetch } from "@/shared/lib/api-client";
import type { CreateFinancialReversalRequest, FinancialReversal, PaginatedResponse } from "@gestorfrete/types";

export interface ListFinancialReversalsParams {
  page?: number;
  limit?: number;
  invoice_id?: string;
  accounts_payable_id?: string;
  accounts_receivable_id?: string;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listFinancialReversals(params: ListFinancialReversalsParams = {}): Promise<PaginatedResponse<FinancialReversal>> {
  return apiFetch<PaginatedResponse<FinancialReversal>>(`/estornos-financeiros${toQuery(params)}`);
}

export function getFinancialReversal(id: string): Promise<FinancialReversal> {
  return apiFetch<FinancialReversal>(`/estornos-financeiros/${id}`);
}

export function createFinancialReversal(body: CreateFinancialReversalRequest): Promise<FinancialReversal> {
  return apiFetch<FinancialReversal>("/estornos-financeiros", { method: "POST", body });
}
