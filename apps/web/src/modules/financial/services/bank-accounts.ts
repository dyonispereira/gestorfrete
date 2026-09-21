import { apiFetch } from "@/shared/lib/api-client";
import type {
  BankAccount,
  BankAccountBalance,
  CreateBankAccountRequest,
  PaginatedResponse,
  UpdateBankAccountRequest,
} from "@gestorfrete/types";

export interface ListBankAccountsParams {
  page?: number;
  limit?: number;
  status?: string;
  type?: string;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listBankAccounts(params: ListBankAccountsParams = {}): Promise<PaginatedResponse<BankAccount>> {
  return apiFetch<PaginatedResponse<BankAccount>>(`/contas-bancarias${toQuery(params)}`);
}

export function getBankAccount(id: string): Promise<BankAccount> {
  return apiFetch<BankAccount>(`/contas-bancarias/${id}`);
}

export function getBankAccountBalance(id: string): Promise<BankAccountBalance> {
  return apiFetch<BankAccountBalance>(`/contas-bancarias/${id}/saldo`);
}

export function createBankAccount(body: CreateBankAccountRequest): Promise<BankAccount> {
  return apiFetch<BankAccount>("/contas-bancarias", { method: "POST", body });
}

export function updateBankAccount(id: string, body: UpdateBankAccountRequest): Promise<BankAccount> {
  return apiFetch<BankAccount>(`/contas-bancarias/${id}`, { method: "PATCH", body });
}

export function deleteBankAccount(id: string): Promise<void> {
  return apiFetch<void>(`/contas-bancarias/${id}`, { method: "DELETE" });
}
