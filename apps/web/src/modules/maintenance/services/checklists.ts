import { apiFetch } from "@/shared/lib/api-client";
import type {
  Checklist,
  CreateChecklistRequest,
  PaginatedResponse,
  RejectChecklistRequest,
  SubmitChecklistRequest,
} from "@gestorfrete/types";

export interface ListChecklistsParams {
  page?: number;
  limit?: number;
  reference_type?: string;
  reference_id?: string;
  type?: string;
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

export function listChecklists(params: ListChecklistsParams = {}): Promise<PaginatedResponse<Checklist>> {
  return apiFetch<PaginatedResponse<Checklist>>(`/checklists${toQuery(params)}`);
}

export function getChecklist(id: string): Promise<Checklist> {
  return apiFetch<Checklist>(`/checklists/${id}`);
}

/** Nasce PENDENTE. Quando `type=MOTORISTA_SAIDA` e `reference_type=VIAGEM`, esta criação é quem
 * dispara `PLANEJADA→AGUARDANDO_CHECKLIST` na viagem — não o preenchimento. */
export function createChecklist(body: CreateChecklistRequest): Promise<Checklist> {
  return apiFetch<Checklist>("/checklists", { method: "POST", body });
}

export function startChecklist(id: string): Promise<Checklist> {
  return apiFetch<Checklist>(`/checklists/${id}/commands/start`, { method: "POST" });
}

export function submitChecklist(id: string, body: SubmitChecklistRequest): Promise<Checklist> {
  return apiFetch<Checklist>(`/checklists/${id}/commands/submit`, { method: "POST", body });
}

/** Quando `type=MOTORISTA_SAIDA`/`VIAGEM`, fecha `AGUARDANDO_CHECKLIST→LIBERADA` na viagem. */
export function approveChecklist(id: string): Promise<Checklist> {
  return apiFetch<Checklist>(`/checklists/${id}/commands/approve`, { method: "POST" });
}

/** Sempre cria um novo Checklist PENDENTE referenciando este — nunca reabre. */
export function rejectChecklist(id: string, body: RejectChecklistRequest): Promise<Checklist> {
  return apiFetch<Checklist>(`/checklists/${id}/commands/reject`, { method: "POST", body });
}
