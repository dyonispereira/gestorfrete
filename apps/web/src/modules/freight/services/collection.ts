import { apiFetch } from "@/shared/lib/api-client";
import type { Collection, RegisterCollectionRequest } from "@gestorfrete/types";

export function registerCollection(tripId: string, body: RegisterCollectionRequest): Promise<Collection> {
  return apiFetch<Collection>(`/viagens/${tripId}/coletas`, { method: "POST", body });
}
