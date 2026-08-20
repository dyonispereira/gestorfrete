"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as vehiclesService from "@/modules/fleet/services/vehicles";
import type { CreateVehicleRequest, UpdateVehicleRequest } from "@gestorfrete/types";

export function useVehiclesQuery(params: vehiclesService.ListVehiclesParams) {
  return useQuery({
    queryKey: ["vehicles", "list", params],
    queryFn: () => vehiclesService.listVehicles(params),
  });
}

export function useVehicleQuery(vehicleId: string | undefined) {
  return useQuery({
    queryKey: ["vehicles", vehicleId],
    queryFn: () => vehiclesService.getVehicle(vehicleId as string),
    enabled: Boolean(vehicleId),
  });
}

export function useCreateVehicleMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateVehicleRequest) => vehiclesService.createVehicle(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["vehicles", "list"] }),
  });
}

export function useUpdateVehicleMutation(vehicleId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: UpdateVehicleRequest) => vehiclesService.updateVehicle(vehicleId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vehicles", "list"] });
      queryClient.invalidateQueries({ queryKey: ["vehicles", vehicleId] });
    },
  });
}

export function useDeleteVehicleMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vehicleId: string) => vehiclesService.deleteVehicle(vehicleId),
    onSuccess: (_data, vehicleId) => {
      queryClient.invalidateQueries({ queryKey: ["vehicles", "list"] });
      queryClient.invalidateQueries({ queryKey: ["vehicles", vehicleId] });
    },
  });
}
