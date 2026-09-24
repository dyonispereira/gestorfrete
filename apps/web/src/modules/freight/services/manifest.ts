import { apiFetch } from "@/shared/lib/api-client";
import type { ConfirmManifestRequest, Manifest } from "@gestorfrete/types";

export function confirmManifest(tripId: string, body: ConfirmManifestRequest): Promise<Manifest> {
  return apiFetch<Manifest>(`/viagens/${tripId}/romaneios`, { method: "POST", body });
}
