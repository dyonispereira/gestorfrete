import { apiFetch } from "@/shared/lib/api-client";
import type { TripFinancialsView } from "@gestorfrete/types";

/** D389 — requires `freight.trip.view` plus at least one `financial.trip_*.view` permission; unheld field groups come back `null`, never a partial 403. */
export function getTripFinancials(tripId: string): Promise<TripFinancialsView> {
  return apiFetch<TripFinancialsView>(`/viagens/${tripId}/financeiro`);
}
