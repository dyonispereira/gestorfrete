"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as vehicleDocumentsService from "@/modules/fleet/services/vehicle-documents";
import type { CreateVehicleDocumentRequest, UpdateVehicleDocumentRequest } from "@gestorfrete/types";

export function useVehicleDocumentsQuery(vehicleId: string | undefined) {
  return useQuery({
    queryKey: ["vehicles", vehicleId, "documents"],
    queryFn: () => vehicleDocumentsService.listVehicleDocuments(vehicleId as string),
    enabled: Boolean(vehicleId),
  });
}

function useInvalidateVehicleDocuments(vehicleId: string) {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: ["vehicles", vehicleId, "documents"] });
}

export function useCreateVehicleDocumentMutation(vehicleId: string) {
  const invalidate = useInvalidateVehicleDocuments(vehicleId);
  return useMutation({
    mutationFn: (body: CreateVehicleDocumentRequest) => vehicleDocumentsService.createVehicleDocument(vehicleId, body),
    onSuccess: invalidate,
  });
}

/** No delete mutation — no DELETE endpoint exists for vehicle documents. */
export function useUpdateVehicleDocumentMutation(vehicleId: string) {
  const invalidate = useInvalidateVehicleDocuments(vehicleId);
  return useMutation({
    mutationFn: ({ documentId, body }: { documentId: string; body: UpdateVehicleDocumentRequest }) =>
      vehicleDocumentsService.updateVehicleDocument(vehicleId, documentId, body),
    onSuccess: invalidate,
  });
}
