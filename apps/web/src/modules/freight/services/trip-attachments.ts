import { apiFetch } from "@/shared/lib/api-client";
import type { CreateAttachmentRequest, PaginatedResponse, TripAttachment } from "@gestorfrete/types";

export function listTripAttachments(tripId: string): Promise<PaginatedResponse<TripAttachment>> {
  return apiFetch<PaginatedResponse<TripAttachment>>(`/viagens/${tripId}/attachments`);
}

/** Route requires `freight.trip.edit`; the handler additionally requires `storage.attachment.create` — gate on both. No PATCH — create/delete only. */
export function createTripAttachment(tripId: string, body: CreateAttachmentRequest): Promise<TripAttachment> {
  return apiFetch<TripAttachment>(`/viagens/${tripId}/attachments`, { method: "POST", body });
}

/** Route requires `freight.trip.edit`; the handler additionally requires `storage.attachment.delete`. */
export function deleteTripAttachment(tripId: string, attachmentId: string): Promise<void> {
  return apiFetch<void>(`/viagens/${tripId}/attachments/${attachmentId}`, { method: "DELETE" });
}
