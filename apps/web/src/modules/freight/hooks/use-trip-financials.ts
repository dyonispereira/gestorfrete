"use client";

import { useQuery } from "@tanstack/react-query";

import * as tripFinancialsService from "@/modules/freight/services/trip-financials";

export function useTripFinancialsQuery(tripId: string | undefined) {
  return useQuery({
    queryKey: ["trips", tripId, "financeiro"],
    queryFn: () => tripFinancialsService.getTripFinancials(tripId as string),
    enabled: Boolean(tripId),
    retry: false,
  });
}
