"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as occurrencesService from "@/modules/freight/services/occurrences";
import type { CreateOccurrenceRequest, UpdateOccurrenceRequest } from "@gestorfrete/types";

export function useOccurrencesQuery(tripId: string | undefined, params: occurrencesService.ListOccurrencesParams = {}) {
  return useQuery({
    queryKey: ["trips", tripId, "occurrences", params],
    queryFn: () => occurrencesService.listOccurrences(tripId as string, params),
    enabled: Boolean(tripId),
  });
}

function invalidateOccurrences(queryClient: ReturnType<typeof useQueryClient>, tripId: string) {
  queryClient.invalidateQueries({ queryKey: ["trips", tripId, "occurrences"] });
  queryClient.invalidateQueries({ queryKey: ["trips", tripId, "timeline"] });
}

export function useCreateOccurrenceMutation(tripId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateOccurrenceRequest) => occurrencesService.createOccurrence(tripId, body),
    onSuccess: () => invalidateOccurrences(queryClient, tripId),
  });
}

export function useUpdateOccurrenceMutation(tripId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ occurrenceId, body }: { occurrenceId: string; body: UpdateOccurrenceRequest }) =>
      occurrencesService.updateOccurrence(tripId, occurrenceId, body),
    onSuccess: () => invalidateOccurrences(queryClient, tripId),
  });
}
