import { apiFetch } from "@/shared/lib/api-client";
import type { CreateReferencedNfeRequest, PaginatedResponse, ReferencedNfe } from "@gestorfrete/types";

export function listReferencedNfes(cteId: string): Promise<PaginatedResponse<ReferencedNfe>> {
  return apiFetch<PaginatedResponse<ReferencedNfe>>(`/ctes/${cteId}/nfe-referenciadas`);
}

export function getReferencedNfe(cteId: string, nfeId: string): Promise<ReferencedNfe> {
  return apiFetch<ReferencedNfe>(`/ctes/${cteId}/nfe-referenciadas/${nfeId}`);
}

/** Sem gate de status do CT-e pai — reachable em qualquer status. */
export function createReferencedNfe(cteId: string, body: CreateReferencedNfeRequest): Promise<ReferencedNfe> {
  return apiFetch<ReferencedNfe>(`/ctes/${cteId}/nfe-referenciadas`, { method: "POST", body });
}
