"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as tripAttachmentsService from "@/modules/freight/services/trip-attachments";
import type { CreateAttachmentRequest } from "@gestorfrete/types";

export function useTripAttachmentsQuery(tripId: string | undefined) {
  return useQuery({
    queryKey: ["trips", tripId, "attachments"],
    queryFn: () => tripAttachmentsService.listTripAttachments(tripId as string),
    enabled: Boolean(tripId),
  });
}

function invalidateAttachments(queryClient: ReturnType<typeof useQueryClient>, tripId: string) {
  queryClient.invalidateQueries({ queryKey: ["trips", tripId, "attachments"] });
  queryClient.invalidateQueries({ queryKey: ["trips", tripId, "timeline"] });
}

export function useCreateTripAttachmentMutation(tripId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateAttachmentRequest) => tripAttachmentsService.createTripAttachment(tripId, body),
    onSuccess: () => invalidateAttachments(queryClient, tripId),
  });
}

export function useDeleteTripAttachmentMutation(tripId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (attachmentId: string) => tripAttachmentsService.deleteTripAttachment(tripId, attachmentId),
    onSuccess: () => invalidateAttachments(queryClient, tripId),
  });
}
