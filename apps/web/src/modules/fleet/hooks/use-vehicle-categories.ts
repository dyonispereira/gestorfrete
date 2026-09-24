"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as vehicleCategoriesService from "@/modules/fleet/services/vehicle-categories";
import type { CreateVehicleCategoryRequest, UpdateVehicleCategoryRequest } from "@gestorfrete/types";

export function useVehicleCategoriesQuery(params: vehicleCategoriesService.ListVehicleCategoriesParams = {}) {
  return useQuery({
    queryKey: ["vehicle-categories", "list", params],
    queryFn: () => vehicleCategoriesService.listVehicleCategories(params),
  });
}

export function useCreateVehicleCategoryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateVehicleCategoryRequest) => vehicleCategoriesService.createVehicleCategory(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["vehicle-categories", "list"] }),
  });
}

export function useUpdateVehicleCategoryMutation(vehicleCategoryId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: UpdateVehicleCategoryRequest) =>
      vehicleCategoriesService.updateVehicleCategory(vehicleCategoryId, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["vehicle-categories", "list"] }),
  });
}
