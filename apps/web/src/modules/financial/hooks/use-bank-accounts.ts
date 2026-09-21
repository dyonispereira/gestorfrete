"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as bankAccountsService from "@/modules/financial/services/bank-accounts";
import type { CreateBankAccountRequest, UpdateBankAccountRequest } from "@gestorfrete/types";

export function useBankAccountsListQuery(params: bankAccountsService.ListBankAccountsParams) {
  return useQuery({
    queryKey: ["bank-accounts", "list", params],
    queryFn: () => bankAccountsService.listBankAccounts(params),
  });
}

export function useBankAccountQuery(id: string | undefined) {
  return useQuery({
    queryKey: ["bank-accounts", id],
    queryFn: () => bankAccountsService.getBankAccount(id as string),
    enabled: Boolean(id),
  });
}

export function useBankAccountBalanceQuery(id: string | undefined) {
  return useQuery({
    queryKey: ["bank-accounts", id, "saldo"],
    queryFn: () => bankAccountsService.getBankAccountBalance(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateBankAccountMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateBankAccountRequest) => bankAccountsService.createBankAccount(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["bank-accounts", "list"] }),
  });
}

export function useUpdateBankAccountMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateBankAccountRequest }) =>
      bankAccountsService.updateBankAccount(id, body),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["bank-accounts", "list"] });
      queryClient.invalidateQueries({ queryKey: ["bank-accounts", id] });
    },
  });
}

export function useDeleteBankAccountMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => bankAccountsService.deleteBankAccount(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["bank-accounts", "list"] }),
  });
}
