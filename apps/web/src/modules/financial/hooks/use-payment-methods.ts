"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as paymentMethodService from "@/modules/financial/services/payment-methods";
import type { ListPaymentMethodsParams } from "@/modules/financial/services/payment-methods";
import type { CreatePaymentMethodRequest, UpdatePaymentMethodRequest } from "@gestorfrete/types";

export function usePaymentMethodsListQuery(params: ListPaymentMethodsParams = {}) {
  return useQuery({
    queryKey: ["formas-pagamento", params],
    queryFn: () => paymentMethodService.listPaymentMethods(params),
  });
}

export function usePaymentMethodQuery(id: string | undefined) {
  return useQuery({
    queryKey: ["formas-pagamento", id],
    queryFn: () => paymentMethodService.getPaymentMethod(id as string),
    enabled: Boolean(id),
  });
}

export function useCreatePaymentMethodMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreatePaymentMethodRequest) => paymentMethodService.createPaymentMethod(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["formas-pagamento"] }),
  });
}

export function useUpdatePaymentMethodMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdatePaymentMethodRequest }) =>
      paymentMethodService.updatePaymentMethod(id, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["formas-pagamento"] }),
  });
}
