import { apiFetch } from "@/shared/lib/api-client";
import type { ChartOfAccounts, CreateChartOfAccountsRequest, PaginatedResponse, UpdateChartOfAccountsRequest } from "@gestorfrete/types";

export interface ListChartOfAccountsParams {
  page?: number;
  limit?: number;
  search?: string;
  type?: string;
  parent_id?: string;
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

export function listChartOfAccounts(params: ListChartOfAccountsParams = {}): Promise<PaginatedResponse<ChartOfAccounts>> {
  return apiFetch<PaginatedResponse<ChartOfAccounts>>(`/plano-contas${toQuery(params)}`);
}

export function getChartOfAccounts(id: string): Promise<ChartOfAccounts> {
  return apiFetch<ChartOfAccounts>(`/plano-contas/${id}`);
}

export function createChartOfAccounts(body: CreateChartOfAccountsRequest): Promise<ChartOfAccounts> {
  return apiFetch<ChartOfAccounts>("/plano-contas", { method: "POST", body });
}

export function updateChartOfAccounts(id: string, body: UpdateChartOfAccountsRequest): Promise<ChartOfAccounts> {
  return apiFetch<ChartOfAccounts>(`/plano-contas/${id}`, { method: "PATCH", body });
}

export function deleteChartOfAccounts(id: string): Promise<void> {
  return apiFetch<void>(`/plano-contas/${id}`, { method: "DELETE" });
}
