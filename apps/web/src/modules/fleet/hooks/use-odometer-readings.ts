"use client";

import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import * as odometerReadingsService from "@/modules/fleet/services/odometer-readings";
import type { CreateOdometerReadingRequest } from "@gestorfrete/types";

/**
 * Cursor-paginated ("Carregar mais"), not offset — the only Time Series list in this Lote. No
 * update/delete mutation exists — append-only, matches the Backend having none.
 */
export function useOdometerReadingsQuery(vehicleId: string | undefined, origem?: string) {
  return useInfiniteQuery({
    queryKey: ["vehicles", vehicleId, "odometer-readings", origem],
    queryFn: ({ pageParam }: { pageParam: string | undefined }) =>
      odometerReadingsService.listOdometerReadings(vehicleId as string, { cursor: pageParam, origem }),
    enabled: Boolean(vehicleId),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => (lastPage.meta.pagination.has_more ? lastPage.meta.pagination.next_cursor : undefined),
  });
}

export function useCreateOdometerReadingMutation(vehicleId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateOdometerReadingRequest) => odometerReadingsService.createOdometerReading(vehicleId, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["vehicles", vehicleId, "odometer-readings"] }),
  });
}
