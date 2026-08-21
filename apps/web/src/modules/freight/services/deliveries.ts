import { apiFetch } from "@/shared/lib/api-client";
import type {
  CreateDeliveryRequest,
  Delivery,
  PaginatedResponse,
  ProofOfDelivery,
  RegisterProofOfDeliveryRequest,
  UpdateDeliveryRequest,
} from "@gestorfrete/types";

export function listDeliveries(tripId: string): Promise<PaginatedResponse<Delivery>> {
  return apiFetch<PaginatedResponse<Delivery>>(`/viagens/${tripId}/entregas`);
}

export function getDelivery(tripId: string, deliveryId: string): Promise<Delivery> {
  return apiFetch<Delivery>(`/viagens/${tripId}/entregas/${deliveryId}`);
}

export function createDelivery(tripId: string, body: CreateDeliveryRequest): Promise<Delivery> {
  return apiFetch<Delivery>(`/viagens/${tripId}/entregas`, { method: "POST", body });
}

/** The one sub-resource where `status` IS directly PATCH-editable — `RECUSADA` requires `rejection_reason`. */
export function updateDelivery(tripId: string, deliveryId: string, body: UpdateDeliveryRequest): Promise<Delivery> {
  return apiFetch<Delivery>(`/viagens/${tripId}/entregas/${deliveryId}`, { method: "PATCH", body });
}

/** 1:1 with Delivery, no update/delete — immutable once registered. */
export function registerProofOfDelivery(
  tripId: string,
  deliveryId: string,
  body: RegisterProofOfDeliveryRequest = {}
): Promise<ProofOfDelivery> {
  return apiFetch<ProofOfDelivery>(`/viagens/${tripId}/entregas/${deliveryId}/canhoto`, { method: "POST", body });
}
