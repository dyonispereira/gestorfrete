import { apiFetch } from "@/shared/lib/api-client";
import type { CursorPaginatedResponse, FiscalEvent } from "@gestorfrete/types";

export interface ListFiscalEventsParams {
  cursor?: string;
  limit?: number;
  document_type?: string;
  document_id?: string;
  external_protocol?: string;
  result?: string;
  origin?: string;
  attempt_number?: number;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

/**
 * D277 — 100% somente leitura, nenhum comando de "consultar SEFAZ agora" existe. Em ambientes sem
 * o simulador de resposta SEFAZ acionado, esta lista fica genuinamente vazia — mostrada como dado
 * real de API mesmo assim, mesmo precedente de honestidade da Disponibilidade (Lote Frota).
 */
export function listFiscalEvents(params: ListFiscalEventsParams = {}): Promise<CursorPaginatedResponse<FiscalEvent>> {
  return apiFetch<CursorPaginatedResponse<FiscalEvent>>(`/fiscal/events${toQuery(params)}`);
}
