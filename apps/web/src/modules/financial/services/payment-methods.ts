import { apiFetch } from "@/shared/lib/api-client";
import type { CreatePaymentMethodRequest, PaginatedResponse, PaymentMethod, UpdatePaymentMethodRequest } from "@gestorfrete/types";

export interface ListPaymentMethodsParams {
  page?: number;
  limit?: number;
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

export function listPaymentMethods(params: ListPaymentMethodsParams = {}): Promise<PaginatedResponse<PaymentMethod>> {
  return apiFetch<PaginatedResponse<PaymentMethod>>(`/formas-pagamento${toQuery(params)}`);
}

export function getPaymentMethod(id: string): Promise<PaymentMethod> {
  return apiFetch<PaymentMethod>(`/formas-pagamento/${id}`);
}

export function createPaymentMethod(body: CreatePaymentMethodRequest): Promise<PaymentMethod> {
  return apiFetch<PaymentMethod>("/formas-pagamento", { method: "POST", body });
}

export function updatePaymentMethod(id: string, body: UpdatePaymentMethodRequest): Promise<PaymentMethod> {
  return apiFetch<PaymentMethod>(`/formas-pagamento/${id}`, { method: "PATCH", body });
}
