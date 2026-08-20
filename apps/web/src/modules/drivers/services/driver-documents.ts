import { apiFetch } from "@/shared/lib/api-client";
import type { CreateDriverDocumentRequest, DriverDocument, PaginatedResponse, UpdateDriverDocumentRequest } from "@gestorfrete/types";

export function listDriverDocuments(driverId: string): Promise<PaginatedResponse<DriverDocument>> {
  return apiFetch<PaginatedResponse<DriverDocument>>(`/drivers/${driverId}/documents`);
}

export function createDriverDocument(driverId: string, body: CreateDriverDocumentRequest): Promise<DriverDocument> {
  return apiFetch<DriverDocument>(`/drivers/${driverId}/documents`, { method: "POST", body });
}

export function updateDriverDocument(
  driverId: string,
  documentId: string,
  body: UpdateDriverDocumentRequest
): Promise<DriverDocument> {
  return apiFetch<DriverDocument>(`/drivers/${driverId}/documents/${documentId}`, { method: "PATCH", body });
}

export function deleteDriverDocument(driverId: string, documentId: string): Promise<void> {
  return apiFetch<void>(`/drivers/${driverId}/documents/${documentId}`, { method: "DELETE" });
}
