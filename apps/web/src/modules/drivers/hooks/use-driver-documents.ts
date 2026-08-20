"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as driverDocumentsService from "@/modules/drivers/services/driver-documents";
import type { CreateDriverDocumentRequest, UpdateDriverDocumentRequest } from "@gestorfrete/types";

export function useDriverDocumentsQuery(driverId: string | undefined) {
  return useQuery({
    queryKey: ["drivers", driverId, "documents"],
    queryFn: () => driverDocumentsService.listDriverDocuments(driverId as string),
    enabled: Boolean(driverId),
  });
}

function useInvalidateDriverDocuments(driverId: string) {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: ["drivers", driverId, "documents"] });
}

export function useCreateDriverDocumentMutation(driverId: string) {
  const invalidate = useInvalidateDriverDocuments(driverId);
  return useMutation({
    mutationFn: (body: CreateDriverDocumentRequest) => driverDocumentsService.createDriverDocument(driverId, body),
    onSuccess: invalidate,
  });
}

export function useUpdateDriverDocumentMutation(driverId: string) {
  const invalidate = useInvalidateDriverDocuments(driverId);
  return useMutation({
    mutationFn: ({ documentId, body }: { documentId: string; body: UpdateDriverDocumentRequest }) =>
      driverDocumentsService.updateDriverDocument(driverId, documentId, body),
    onSuccess: invalidate,
  });
}

export function useDeleteDriverDocumentMutation(driverId: string) {
  const invalidate = useInvalidateDriverDocuments(driverId);
  return useMutation({
    mutationFn: (documentId: string) => driverDocumentsService.deleteDriverDocument(driverId, documentId),
    onSuccess: invalidate,
  });
}
