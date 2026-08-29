import { apiFetch } from "@/shared/lib/api-client";
import type { CursorPaginatedResponse, StatusHistoryEntry } from "@gestorfrete/types";

export interface ListWorkOrderStatusHistoryParams {
  cursor?: string;
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

export function listWorkOrderStatusHistory(
  workOrderId: string,
  params: ListWorkOrderStatusHistoryParams = {}
): Promise<CursorPaginatedResponse<StatusHistoryEntry>> {
  return apiFetch<CursorPaginatedResponse<StatusHistoryEntry>>(`/ordens-servico/${workOrderId}/status-history${toQuery(params)}`);
}
