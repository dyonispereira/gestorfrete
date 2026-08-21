import { apiFetch } from "@/shared/lib/api-client";
import type { CursorPaginatedResponse, TripTimelineEntry } from "@gestorfrete/types";

export interface ListTripTimelineParams {
  cursor?: string;
  limit?: number;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

/** GET-only, forever (D187/D236) — no write path exists or is planned for this resource. */
export function listTripTimeline(
  tripId: string,
  params: ListTripTimelineParams = {}
): Promise<CursorPaginatedResponse<TripTimelineEntry>> {
  return apiFetch<CursorPaginatedResponse<TripTimelineEntry>>(`/viagens/${tripId}/timeline${toQuery(params)}`);
}
