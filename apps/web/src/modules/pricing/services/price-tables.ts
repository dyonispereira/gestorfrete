import { apiFetch } from "@/shared/lib/api-client";
import type {
  CreatePriceTableItemRequest,
  CreatePriceTableRequest,
  PaginatedResponse,
  PriceTable,
  PriceTableItem,
  UpdatePriceTableRequest,
} from "@gestorfrete/types";

export interface ListPriceTablesParams {
  page?: number;
  limit?: number;
  direcao?: string;
  status?: string;
  cliente_id?: string;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listPriceTables(params: ListPriceTablesParams = {}): Promise<PaginatedResponse<PriceTable>> {
  return apiFetch<PaginatedResponse<PriceTable>>(`/tabelas-preco${toQuery(params)}`);
}

export function getPriceTable(id: string): Promise<PriceTable> {
  return apiFetch<PriceTable>(`/tabelas-preco/${id}`);
}

export function createPriceTable(body: CreatePriceTableRequest): Promise<PriceTable> {
  return apiFetch<PriceTable>("/tabelas-preco", { method: "POST", body });
}

export function updatePriceTable(id: string, body: UpdatePriceTableRequest): Promise<PriceTable> {
  return apiFetch<PriceTable>(`/tabelas-preco/${id}`, { method: "PATCH", body });
}

export function activatePriceTable(id: string): Promise<PriceTable> {
  return apiFetch<PriceTable>(`/tabelas-preco/${id}/commands/activate`, { method: "POST" });
}

export function expirePriceTable(id: string): Promise<PriceTable> {
  return apiFetch<PriceTable>(`/tabelas-preco/${id}/commands/expire`, { method: "POST" });
}

export async function listPriceTableItems(priceTableId: string): Promise<PriceTableItem[]> {
  const response = await apiFetch<{ data: PriceTableItem[] }>(`/tabelas-preco/${priceTableId}/itens`);
  return response.data;
}

export function createPriceTableItem(
  priceTableId: string,
  body: CreatePriceTableItemRequest
): Promise<PriceTableItem> {
  return apiFetch<PriceTableItem>(`/tabelas-preco/${priceTableId}/itens`, { method: "POST", body });
}

export function deletePriceTableItem(priceTableId: string, itemId: string): Promise<void> {
  return apiFetch<void>(`/tabelas-preco/${priceTableId}/itens/${itemId}`, { method: "DELETE" });
}
