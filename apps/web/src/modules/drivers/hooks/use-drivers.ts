"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as driversService from "@/modules/drivers/services/drivers";
import type { CreateDriverRequest, UpdateDriverRequest } from "@gestorfrete/types";

export function useDriversQuery(params: driversService.ListDriversParams) {
  return useQuery({
    queryKey: ["drivers", "list", params],
    queryFn: () => driversService.listDrivers(params),
  });
}

export function useDriverQuery(driverId: string | undefined) {
  return useQuery({
    queryKey: ["drivers", driverId],
    queryFn: () => driversService.getDriver(driverId as string),
    enabled: Boolean(driverId),
  });
}

export function useCreateDriverMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateDriverRequest) => driversService.createDriver(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["drivers", "list"] }),
  });
}

function useInvalidateDriver(driverId: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ["drivers", "list"] });
    queryClient.invalidateQueries({ queryKey: ["drivers", driverId] });
  };
}

export function useUpdateDriverMutation(driverId: string) {
  const invalidate = useInvalidateDriver(driverId);
  return useMutation({
    mutationFn: (body: UpdateDriverRequest) => driversService.updateDriver(driverId, body),
    onSuccess: invalidate,
  });
}

export function useDeleteDriverMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (driverId: string) => driversService.deleteDriver(driverId),
    onSuccess: (_data, driverId) => {
      queryClient.invalidateQueries({ queryKey: ["drivers", "list"] });
      queryClient.invalidateQueries({ queryKey: ["drivers", driverId] });
    },
  });
}

export function useBlockDriverMutation(driverId: string) {
  const invalidate = useInvalidateDriver(driverId);
  return useMutation({
    mutationFn: () => driversService.blockDriver(driverId),
    onSuccess: invalidate,
  });
}

export function useUnblockDriverMutation(driverId: string) {
  const invalidate = useInvalidateDriver(driverId);
  return useMutation({
    mutationFn: () => driversService.unblockDriver(driverId),
    onSuccess: invalidate,
  });
}
