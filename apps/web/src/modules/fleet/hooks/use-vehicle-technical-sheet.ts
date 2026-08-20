"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as technicalSheetService from "@/modules/fleet/services/vehicle-technical-sheet";
import type { UpsertVehicleTechnicalSheetRequest } from "@gestorfrete/types";

export function useVehicleTechnicalSheetQuery(vehicleId: string | undefined) {
  return useQuery({
    queryKey: ["vehicles", vehicleId, "technical-sheet"],
    queryFn: () => technicalSheetService.getVehicleTechnicalSheet(vehicleId as string),
    enabled: Boolean(vehicleId),
    retry: false,
  });
}

export function useUpsertVehicleTechnicalSheetMutation(vehicleId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: UpsertVehicleTechnicalSheetRequest) => technicalSheetService.upsertVehicleTechnicalSheet(vehicleId, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["vehicles", vehicleId, "technical-sheet"] }),
  });
}
