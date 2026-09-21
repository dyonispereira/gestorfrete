import { apiFetch } from "@/shared/lib/api-client";
import type {
  AccountsReceivable,
  ConfirmReceiptRequest,
  CreateAccountsReceivableRequest,
  PaginatedResponse,
  UpdateAccountsReceivableRequest,
} from "@gestorfrete/types";

export function listAccountsReceivableForInvoice(invoiceId: string): Promise<PaginatedResponse<AccountsReceivable>> {
  return apiFetch<PaginatedResponse<AccountsReceivable>>(`/faturas/${invoiceId}/contas-receber`);
}

/** `GET /contas-receber` agregado entre Faturas (Lote Financeiro, Parte 2.1) — "o que tenho para
 * receber hoje" sem abrir Fatura por Fatura. Ownership não muda (continua sub-recurso de Fatura). */
export interface ListAccountsReceivableGlobalParams {
  page?: number;
  limit?: number;
  status?: string;
  client_id?: string;
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

export function listAccountsReceivableGlobal(
  params: ListAccountsReceivableGlobalParams = {}
): Promise<PaginatedResponse<AccountsReceivable>> {
  return apiFetch<PaginatedResponse<AccountsReceivable>>(`/contas-receber${toQuery(params)}`);
}

export function getAccountsReceivable(invoiceId: string, id: string): Promise<AccountsReceivable> {
  return apiFetch<AccountsReceivable>(`/faturas/${invoiceId}/contas-receber/${id}`);
}

export function createAccountsReceivable(
  invoiceId: string, body: CreateAccountsReceivableRequest
): Promise<AccountsReceivable> {
  return apiFetch<AccountsReceivable>(`/faturas/${invoiceId}/contas-receber`, { method: "POST", body });
}

export function updateAccountsReceivable(
  invoiceId: string, id: string, body: UpdateAccountsReceivableRequest
): Promise<AccountsReceivable> {
  return apiFetch<AccountsReceivable>(`/faturas/${invoiceId}/contas-receber/${id}`, { method: "PATCH", body });
}

export function confirmReceiptAccountsReceivable(
  invoiceId: string, id: string, body: ConfirmReceiptRequest
): Promise<AccountsReceivable> {
  return apiFetch<AccountsReceivable>(
    `/faturas/${invoiceId}/contas-receber/${id}/commands/confirm-receipt`, { method: "POST", body }
  );
}
