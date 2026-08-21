import { apiFetch } from "@/shared/lib/api-client";
import type { CreateCommentRequest, PaginatedResponse, TripComment, UpdateCommentRequest } from "@gestorfrete/types";

export function listTripComments(tripId: string, visibleToClient?: boolean): Promise<PaginatedResponse<TripComment>> {
  const query = visibleToClient !== undefined ? `?visible_to_client=${visibleToClient}` : "";
  return apiFetch<PaginatedResponse<TripComment>>(`/viagens/${tripId}/comments${query}`);
}

/** Route requires `freight.trip.view`; the handler additionally requires `storage.comment.create` — gate on both. */
export function createTripComment(tripId: string, body: CreateCommentRequest): Promise<TripComment> {
  return apiFetch<TripComment>(`/viagens/${tripId}/comments`, { method: "POST", body });
}

export function updateTripComment(tripId: string, commentId: string, body: UpdateCommentRequest): Promise<TripComment> {
  return apiFetch<TripComment>(`/viagens/${tripId}/comments/${commentId}`, { method: "PATCH", body });
}

export function deleteTripComment(tripId: string, commentId: string): Promise<void> {
  return apiFetch<void>(`/viagens/${tripId}/comments/${commentId}`, { method: "DELETE" });
}
