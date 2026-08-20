"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as vehicleCompositionsService from "@/modules/fleet/services/vehicle-compositions";
import type { CreateVehicleCompositionRequest } from "@gestorfrete/types";

export function useVehicleCompositionsQuery(params: vehicleCompositionsService.ListVehicleCompositionsParams) {
  return useQuery({
    queryKey: ["vehicle-compositions", "list", params],
    queryFn: () => vehicleCompositionsService.listVehicleCompositions(params),
  });
}

/** No update/delete mutation — D248, creating a new composition auto-closes the previous one server-side. */
export function useCreateVehicleCompositionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateVehicleCompositionRequest) => vehicleCompositionsService.createVehicleComposition(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["vehicle-compositions", "list"] }),
  });
}
