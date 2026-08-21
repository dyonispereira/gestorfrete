"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as deliveriesService from "@/modules/freight/services/deliveries";
import type { CreateDeliveryRequest, RegisterProofOfDeliveryRequest, UpdateDeliveryRequest } from "@gestorfrete/types";

export function useDeliveriesQuery(tripId: string | undefined) {
  return useQuery({
    queryKey: ["trips", tripId, "deliveries"],
    queryFn: () => deliveriesService.listDeliveries(tripId as string),
    enabled: Boolean(tripId),
  });
}

function invalidateDeliveries(queryClient: ReturnType<typeof useQueryClient>, tripId: string) {
  queryClient.invalidateQueries({ queryKey: ["trips", tripId, "deliveries"] });
  queryClient.invalidateQueries({ queryKey: ["trips", tripId] });
  queryClient.invalidateQueries({ queryKey: ["trips", tripId, "timeline"] });
}

export function useCreateDeliveryMutation(tripId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateDeliveryRequest) => deliveriesService.createDelivery(tripId, body),
    onSuccess: () => invalidateDeliveries(queryClient, tripId),
  });
}

export function useUpdateDeliveryMutation(tripId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ deliveryId, body }: { deliveryId: string; body: UpdateDeliveryRequest }) =>
      deliveriesService.updateDelivery(tripId, deliveryId, body),
    onSuccess: () => invalidateDeliveries(queryClient, tripId),
  });
}

export function useRegisterProofOfDeliveryMutation(tripId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ deliveryId, body }: { deliveryId: string; body?: RegisterProofOfDeliveryRequest }) =>
      deliveriesService.registerProofOfDelivery(tripId, deliveryId, body),
    onSuccess: () => invalidateDeliveries(queryClient, tripId),
  });
}
