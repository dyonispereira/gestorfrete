"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as reversalsService from "@/modules/financial/services/financial-reversals";
import type { CreateFinancialReversalRequest } from "@gestorfrete/types";

export function useFinancialReversalsListQuery(params: reversalsService.ListFinancialReversalsParams) {
  return useQuery({
    queryKey: ["financial-reversals", "list", params],
    queryFn: () => reversalsService.listFinancialReversals(params),
  });
}

export function useCreateFinancialReversalMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateFinancialReversalRequest) => reversalsService.createFinancialReversal(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["financial-reversals", "list"] }),
  });
}
