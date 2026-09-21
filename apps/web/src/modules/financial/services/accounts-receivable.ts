import { apiFetch } from "@/shared/lib/api-client";
import type {
  AccountsReceivable,
  ConfirmReceiptRequest,
  CreateAccountsReceivableRequest,
  PaginatedResponse,
  UpdateAccountsReceivableRequest,
} from "@gestorfrete/types";

/** Todas as rotas de Conta a Receber são sub-recurso de Fatura (`fatura_id` obrigatório no
 * backend) — não existe `GET /contas-receber` agregado entre Faturas (ver `accounts-receivable-tab.tsx`). */
export function listAccountsReceivableForInvoice(invoiceId: string): Promise<PaginatedResponse<AccountsReceivable>> {
  return apiFetch<PaginatedResponse<AccountsReceivable>>(`/faturas/${invoiceId}/contas-receber`);
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
