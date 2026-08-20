import { apiFetch } from "@/shared/lib/api-client";
import type { UpsertVehicleTechnicalSheetRequest, VehicleTechnicalSheet } from "@gestorfrete/types";

export function getVehicleTechnicalSheet(vehicleId: string): Promise<VehicleTechnicalSheet> {
  return apiFetch<VehicleTechnicalSheet>(`/veiculos/${vehicleId}/technical-sheet`);
}

export function upsertVehicleTechnicalSheet(
  vehicleId: string,
  body: UpsertVehicleTechnicalSheetRequest
): Promise<VehicleTechnicalSheet> {
  return apiFetch<VehicleTechnicalSheet>(`/veiculos/${vehicleId}/technical-sheet`, { method: "PATCH", body });
}
