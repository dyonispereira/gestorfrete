import { apiFetch } from "@/shared/lib/api-client";
import type { CostCenter, CreateCostCenterRequest, PaginatedResponse, UpdateCostCenterRequest } from "@gestorfrete/types";

export interface ListCostCentersParams {
  page?: number;
  limit?: number;
  status?: string;
  search?: string;
  // branch_id omitted on purpose — no endpoint exists to list Filiais to build a real picker
  // (Lote Cadastros audit); don't add a raw-UUID filter input either.
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listCostCenters(params: ListCostCentersParams = {}): Promise<PaginatedResponse<CostCenter>> {
  return apiFetch<PaginatedResponse<CostCenter>>(`/cost-centers${toQuery(params)}`);
}

export function getCostCenter(id: string): Promise<CostCenter> {
  return apiFetch<CostCenter>(`/cost-centers/${id}`);
}

export function createCostCenter(body: CreateCostCenterRequest): Promise<CostCenter> {
  return apiFetch<CostCenter>("/cost-centers", { method: "POST", body });
}

/** No DELETE endpoint exists — deactivation is `status: "INATIVO"` through this same PATCH. */
export function updateCostCenter(id: string, body: UpdateCostCenterRequest): Promise<CostCenter> {
  return apiFetch<CostCenter>(`/cost-centers/${id}`, { method: "PATCH", body });
}
