"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as tripCommentsService from "@/modules/freight/services/trip-comments";
import type { CreateCommentRequest, UpdateCommentRequest } from "@gestorfrete/types";

export function useTripCommentsQuery(tripId: string | undefined) {
  return useQuery({
    queryKey: ["trips", tripId, "comments"],
    queryFn: () => tripCommentsService.listTripComments(tripId as string),
    enabled: Boolean(tripId),
  });
}

function invalidateComments(queryClient: ReturnType<typeof useQueryClient>, tripId: string) {
  queryClient.invalidateQueries({ queryKey: ["trips", tripId, "comments"] });
  queryClient.invalidateQueries({ queryKey: ["trips", tripId, "timeline"] });
}

export function useCreateTripCommentMutation(tripId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateCommentRequest) => tripCommentsService.createTripComment(tripId, body),
    onSuccess: () => invalidateComments(queryClient, tripId),
  });
}

export function useUpdateTripCommentMutation(tripId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ commentId, body }: { commentId: string; body: UpdateCommentRequest }) =>
      tripCommentsService.updateTripComment(tripId, commentId, body),
    onSuccess: () => invalidateComments(queryClient, tripId),
  });
}

export function useDeleteTripCommentMutation(tripId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (commentId: string) => tripCommentsService.deleteTripComment(tripId, commentId),
    onSuccess: () => invalidateComments(queryClient, tripId),
  });
}
