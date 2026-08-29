"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as workOrderItemsService from "@/modules/maintenance/services/work-order-items";
import type { CreateWorkOrderItemRequest } from "@gestorfrete/types";

export function useWorkOrderItemsQuery(workOrderId: string | undefined) {
  return useQuery({
    queryKey: ["work-orders", workOrderId, "items"],
    queryFn: () => workOrderItemsService.listWorkOrderItems(workOrderId as string),
    enabled: Boolean(workOrderId),
  });
}

export function useCreateWorkOrderItemMutation(workOrderId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateWorkOrderItemRequest) => workOrderItemsService.createWorkOrderItem(workOrderId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["work-orders", workOrderId, "items"] });
      // custo_previsto muda como efeito colateral (recalculado pelo Backend).
      queryClient.invalidateQueries({ queryKey: ["work-orders", workOrderId] });
    },
  });
}
