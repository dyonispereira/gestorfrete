"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as costCentersService from "@/modules/financial/services/cost-centers";
import type { CreateCostCenterRequest, UpdateCostCenterRequest } from "@gestorfrete/types";

export function useCostCentersQuery(params: costCentersService.ListCostCentersParams) {
  return useQuery({
    queryKey: ["cost-centers", "list", params],
    queryFn: () => costCentersService.listCostCenters(params),
  });
}

export function useCostCenterQuery(costCenterId: string | undefined) {
  return useQuery({
    queryKey: ["cost-centers", costCenterId],
    queryFn: () => costCentersService.getCostCenter(costCenterId as string),
    enabled: Boolean(costCenterId),
  });
}

export function useCreateCostCenterMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateCostCenterRequest) => costCentersService.createCostCenter(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["cost-centers", "list"] }),
  });
}

export function useUpdateCostCenterMutation(costCenterId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: UpdateCostCenterRequest) => costCentersService.updateCostCenter(costCenterId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cost-centers", "list"] });
      queryClient.invalidateQueries({ queryKey: ["cost-centers", costCenterId] });
    },
  });
}
