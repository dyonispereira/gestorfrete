"use client";

import { useInfiniteQuery } from "@tanstack/react-query";

import * as tripTimelineService from "@/modules/freight/services/trip-timeline";

/** Cursor-paginated ("Carregar mais"), read-only forever (D187/D236) — no mutation exists. */
export function useTripTimelineQuery(tripId: string | undefined) {
  return useInfiniteQuery({
    queryKey: ["trips", tripId, "timeline"],
    queryFn: ({ pageParam }: { pageParam: string | undefined }) =>
      tripTimelineService.listTripTimeline(tripId as string, { cursor: pageParam }),
    enabled: Boolean(tripId),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => (lastPage.meta.pagination.has_more ? lastPage.meta.pagination.next_cursor : undefined),
  });
}
