import { apiFetch } from "@/shared/lib/api-client";
import type {
  AccountsPayable,
  CreateAccountsPayableRequest,
  ExpenseApproval,
  ExpenseAllocation,
  ExpenseDecisionRequest,
  PayAccountsPayableRequest,
  PaginatedResponse,
  UpdateAccountsPayableRequest,
} from "@gestorfrete/types";

export interface ListAccountsPayableParams {
  page?: number;
  limit?: number;
  status?: string;
  origin?: string;
  supplier_id?: string;
  cost_center_id?: string;
  trip_id?: string;
  // `vehicle_id`/`chart_of_accounts_id`/`accounting_period` — Lote Financeiro, Parte 2.1 (gap
  // registrado na Parte 2: dimensões gravadas na Parte 1 mas não consultáveis, fechado aqui).
  vehicle_id?: string;
  chart_of_accounts_id?: string;
  accounting_period?: string;
  due_date__gte?: string;
  due_date__lte?: string;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listAccountsPayable(params: ListAccountsPayableParams = {}): Promise<PaginatedResponse<AccountsPayable>> {
  return apiFetch<PaginatedResponse<AccountsPayable>>(`/contas-pagar${toQuery(params)}`);
}

export function getAccountsPayable(id: string): Promise<AccountsPayable> {
  return apiFetch<AccountsPayable>(`/contas-pagar/${id}`);
}

export function createAccountsPayable(body: CreateAccountsPayableRequest): Promise<AccountsPayable> {
  return apiFetch<AccountsPayable>("/contas-pagar", { method: "POST", body });
}

export function updateAccountsPayable(id: string, body: UpdateAccountsPayableRequest): Promise<AccountsPayable> {
  return apiFetch<AccountsPayable>(`/contas-pagar/${id}`, { method: "PATCH", body });
}

export function deleteAccountsPayable(id: string): Promise<void> {
  return apiFetch<void>(`/contas-pagar/${id}`, { method: "DELETE" });
}

export function approveAccountsPayable(id: string, body: ExpenseDecisionRequest = {}): Promise<AccountsPayable> {
  return apiFetch<AccountsPayable>(`/contas-pagar/${id}/commands/approve`, { method: "POST", body });
}

export function rejectAccountsPayable(id: string, body: ExpenseDecisionRequest): Promise<AccountsPayable> {
  return apiFetch<AccountsPayable>(`/contas-pagar/${id}/commands/reject`, { method: "POST", body });
}

export function payAccountsPayable(id: string, body: PayAccountsPayableRequest): Promise<AccountsPayable> {
  return apiFetch<AccountsPayable>(`/contas-pagar/${id}/commands/pay`, { method: "POST", body });
}

export function listExpenseApprovals(id: string): Promise<PaginatedResponse<ExpenseApproval>> {
  return apiFetch<PaginatedResponse<ExpenseApproval>>(`/contas-pagar/${id}/aprovacoes`);
}

export function listExpenseAllocations(id: string): Promise<PaginatedResponse<ExpenseAllocation>> {
  return apiFetch<PaginatedResponse<ExpenseAllocation>>(`/contas-pagar/${id}/rateios`);
}
