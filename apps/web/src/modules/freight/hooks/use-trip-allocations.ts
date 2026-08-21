"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as tripAllocationsService from "@/modules/freight/services/trip-allocations";
import type { CreateTripAllocationRequest, ReallocateTripResourcesRequest } from "@gestorfrete/types";

export function useCurrentTripAllocationQuery(tripId: string | undefined) {
  return useQuery({
    queryKey: ["trips", tripId, "resources", "current"],
    queryFn: () => tripAllocationsService.getCurrentTripAllocation(tripId as string),
    enabled: Boolean(tripId),
    retry: false,
  });
}

export function useTripAllocationHistoryQuery(tripId: string | undefined) {
  return useQuery({
    queryKey: ["trips", tripId, "resources", "history"],
    queryFn: () => tripAllocationsService.getTripAllocationHistory(tripId as string),
    enabled: Boolean(tripId),
  });
}

function invalidateAllocations(queryClient: ReturnType<typeof useQueryClient>, tripId: string) {
  queryClient.invalidateQueries({ queryKey: ["trips", tripId, "resources"] });
  queryClient.invalidateQueries({ queryKey: ["trips", tripId] });
  queryClient.invalidateQueries({ queryKey: ["trips", tripId, "timeline"] });
}

export function useCreateTripAllocationMutation(tripId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateTripAllocationRequest) => tripAllocationsService.createTripAllocation(tripId, body),
    onSuccess: () => invalidateAllocations(queryClient, tripId),
  });
}

export function useReallocateTripResourcesMutation(tripId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ReallocateTripResourcesRequest) => tripAllocationsService.reallocateTripResources(tripId, body),
    onSuccess: () => invalidateAllocations(queryClient, tripId),
  });
}
