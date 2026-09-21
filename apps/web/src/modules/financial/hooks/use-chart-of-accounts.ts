"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as chartOfAccountsService from "@/modules/financial/services/chart-of-accounts";
import type { CreateChartOfAccountsRequest, UpdateChartOfAccountsRequest } from "@gestorfrete/types";

export function useChartOfAccountsListQuery(params: chartOfAccountsService.ListChartOfAccountsParams) {
  return useQuery({
    queryKey: ["chart-of-accounts", "list", params],
    queryFn: () => chartOfAccountsService.listChartOfAccounts(params),
  });
}

export function useChartOfAccountsQuery(id: string | undefined) {
  return useQuery({
    queryKey: ["chart-of-accounts", id],
    queryFn: () => chartOfAccountsService.getChartOfAccounts(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateChartOfAccountsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateChartOfAccountsRequest) => chartOfAccountsService.createChartOfAccounts(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["chart-of-accounts", "list"] }),
  });
}

export function useUpdateChartOfAccountsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateChartOfAccountsRequest }) =>
      chartOfAccountsService.updateChartOfAccounts(id, body),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["chart-of-accounts", "list"] });
      queryClient.invalidateQueries({ queryKey: ["chart-of-accounts", id] });
    },
  });
}

export function useDeleteChartOfAccountsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => chartOfAccountsService.deleteChartOfAccounts(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["chart-of-accounts", "list"] }),
  });
}
