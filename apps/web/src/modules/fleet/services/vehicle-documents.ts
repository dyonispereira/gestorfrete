import { apiFetch } from "@/shared/lib/api-client";
import type { CreateVehicleDocumentRequest, PaginatedResponse, UpdateVehicleDocumentRequest, VehicleDocument } from "@gestorfrete/types";

export function listVehicleDocuments(vehicleId: string): Promise<PaginatedResponse<VehicleDocument>> {
  return apiFetch<PaginatedResponse<VehicleDocument>>(`/veiculos/${vehicleId}/documentos`);
}

export function createVehicleDocument(vehicleId: string, body: CreateVehicleDocumentRequest): Promise<VehicleDocument> {
  return apiFetch<VehicleDocument>(`/veiculos/${vehicleId}/documentos`, { method: "POST", body });
}

/** No DELETE endpoint exists for vehicle documents. */
export function updateVehicleDocument(
  vehicleId: string,
  documentId: string,
  body: UpdateVehicleDocumentRequest
): Promise<VehicleDocument> {
  return apiFetch<VehicleDocument>(`/veiculos/${vehicleId}/documentos/${documentId}`, { method: "PATCH", body });
}
