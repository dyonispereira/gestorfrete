"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as tripsService from "@/modules/freight/services/trips";
import type {
  CancelarTripRequest,
  CloseAdministrativeTripRequest,
  CreateTripRequest,
  DispatchTripRequest,
  FinishTripRequest,
  InterromperTripRequest,
  UpdateTripRequest,
} from "@gestorfrete/types";

export function useTripsQuery(params: tripsService.ListTripsParams) {
  return useQuery({
    queryKey: ["trips", "list", params],
    queryFn: () => tripsService.listTrips(params),
  });
}

export function useTripQuery(tripId: string | undefined) {
  return useQuery({
    queryKey: ["trips", tripId],
    queryFn: () => tripsService.getTrip(tripId as string),
    enabled: Boolean(tripId),
  });
}

export function useCreateTripMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateTripRequest) => tripsService.createTrip(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["trips", "list"] }),
  });
}

export function useUpdateTripMutation(tripId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: UpdateTripRequest) => tripsService.updateTrip(tripId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trips", "list"] });
      queryClient.invalidateQueries({ queryKey: ["trips", tripId] });
    },
  });
}

export function useDeleteTripMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (tripId: string) => tripsService.deleteTrip(tripId),
    onSuccess: (_data, tripId) => {
      queryClient.invalidateQueries({ queryKey: ["trips", "list"] });
      queryClient.invalidateQueries({ queryKey: ["trips", tripId] });
    },
  });
}

/**
 * Every command mutation shares this shape: invalidate the list + the item, since every command
 * response already returns the full updated Trip (D238) — no extra fetch needed, just the cache
 * refresh so other views pick it up too.
 */
function useTripCommandMutation<TVariables>(mutationFn: (tripId: string, variables: TVariables) => Promise<unknown>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ tripId, variables }: { tripId: string; variables: TVariables }) => mutationFn(tripId, variables),
    onSuccess: (_data, { tripId }) => {
      queryClient.invalidateQueries({ queryKey: ["trips", "list"] });
      queryClient.invalidateQueries({ queryKey: ["trips", tripId] });
      queryClient.invalidateQueries({ queryKey: ["trips", tripId, "timeline"] });
    },
  });
}

export function useAcceptTripMutation() {
  return useTripCommandMutation<void>((tripId) => tripsService.acceptTrip(tripId));
}

export function useDispatchTripMutation() {
  return useTripCommandMutation<DispatchTripRequest | undefined>((tripId, body) =>
    tripsService.dispatchTrip(tripId, body)
  );
}

export function useStartTripMutation() {
  return useTripCommandMutation<DispatchTripRequest | undefined>((tripId, body) =>
    tripsService.startTrip(tripId, body)
  );
}

export function useFinishTripMutation() {
  return useTripCommandMutation<FinishTripRequest | undefined>((tripId, body) =>
    tripsService.finishTrip(tripId, body)
  );
}

export function useInterromperTripMutation() {
  return useTripCommandMutation<InterromperTripRequest>((tripId, body) => tripsService.interromperTrip(tripId, body));
}

export function useRetomarTripMutation() {
  return useTripCommandMutation<void>((tripId) => tripsService.retomarTrip(tripId));
}

export function useCancelarTripMutation() {
  return useTripCommandMutation<CancelarTripRequest>((tripId, body) => tripsService.cancelarTrip(tripId, body));
}

export function useCloseAdministrativeTripMutation() {
  return useTripCommandMutation<CloseAdministrativeTripRequest>((tripId, body) =>
    tripsService.closeAdministrativeTrip(tripId, body)
  );
}
