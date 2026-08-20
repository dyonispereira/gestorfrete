"use client";

import { useQuery } from "@tanstack/react-query";

import * as vehicleAvailabilityService from "@/modules/fleet/services/vehicle-availability";

/** Pure read model — no mutation hooks exist here at all, matching the Backend exposing zero write endpoints. */
export function useVehicleAvailabilityListQuery(params: vehicleAvailabilityService.ListVehicleAvailabilityParams) {
  return useQuery({
    queryKey: ["vehicle-availability", "list", params],
    queryFn: () => vehicleAvailabilityService.listVehicleAvailability(params),
  });
}

export function useVehicleAvailabilityQuery(vehicleId: string | undefined) {
  return useQuery({
    queryKey: ["vehicle-availability", vehicleId],
    queryFn: () => vehicleAvailabilityService.getVehicleAvailability(vehicleId as string),
    enabled: Boolean(vehicleId),
    staleTime: 30_000,
  });
}
