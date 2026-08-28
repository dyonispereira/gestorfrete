import { apiFetch } from "@/shared/lib/api-client";
import type { CorrectionLetter, CreateCorrectionLetterRequest, PaginatedResponse, XmlReference } from "@gestorfrete/types";

export function listCorrectionLetters(cteId: string): Promise<PaginatedResponse<CorrectionLetter>> {
  return apiFetch<PaginatedResponse<CorrectionLetter>>(`/ctes/${cteId}/cartas-correcao`);
}

export function getCorrectionLetter(cteId: string, letterId: string): Promise<CorrectionLetter> {
  return apiFetch<CorrectionLetter>(`/ctes/${cteId}/cartas-correcao/${letterId}`);
}

/** Só aceita com o CT-e pai AUTORIZADO (D282, 409 `FISCAL_CTE_NOT_AUTHORIZED` fora disso). */
export function createCorrectionLetter(cteId: string, body: CreateCorrectionLetterRequest): Promise<CorrectionLetter> {
  return apiFetch<CorrectionLetter>(`/ctes/${cteId}/cartas-correcao`, { method: "POST", body });
}

export function getCorrectionLetterXml(cteId: string, letterId: string): Promise<XmlReference> {
  return apiFetch<XmlReference>(`/ctes/${cteId}/cartas-correcao/${letterId}/xml`);
}
