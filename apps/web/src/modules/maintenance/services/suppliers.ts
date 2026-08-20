import { apiFetch } from "@/shared/lib/api-client";
import type { CreateSupplierRequest, PaginatedResponse, Supplier, UpdateSupplierRequest } from "@gestorfrete/types";

export interface ListSuppliersParams {
  page?: number;
  limit?: number;
  status?: string;
  category?: string;
  search?: string;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listSuppliers(params: ListSuppliersParams = {}): Promise<PaginatedResponse<Supplier>> {
  return apiFetch<PaginatedResponse<Supplier>>(`/suppliers${toQuery(params)}`);
}

export function getSupplier(id: string): Promise<Supplier> {
  return apiFetch<Supplier>(`/suppliers/${id}`);
}

export function createSupplier(body: CreateSupplierRequest): Promise<Supplier> {
  return apiFetch<Supplier>("/suppliers", { method: "POST", body });
}

export function updateSupplier(id: string, body: UpdateSupplierRequest): Promise<Supplier> {
  return apiFetch<Supplier>(`/suppliers/${id}`, { method: "PATCH", body });
}

export function deleteSupplier(id: string): Promise<void> {
  return apiFetch<void>(`/suppliers/${id}`, { method: "DELETE" });
}
