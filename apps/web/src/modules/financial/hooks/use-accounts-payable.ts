"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as accountsPayableService from "@/modules/financial/services/accounts-payable";
import type {
  CreateAccountsPayableRequest,
  ExpenseDecisionRequest,
  PayAccountsPayableRequest,
  UpdateAccountsPayableRequest,
} from "@gestorfrete/types";

export function useAccountsPayableListQuery(params: accountsPayableService.ListAccountsPayableParams) {
  return useQuery({
    queryKey: ["accounts-payable", "list", params],
    queryFn: () => accountsPayableService.listAccountsPayable(params),
  });
}

export function useAccountsPayableQuery(id: string | undefined) {
  return useQuery({
    queryKey: ["accounts-payable", id],
    queryFn: () => accountsPayableService.getAccountsPayable(id as string),
    enabled: Boolean(id),
  });
}

export function useExpenseApprovalsQuery(id: string | undefined) {
  return useQuery({
    queryKey: ["accounts-payable", id, "aprovacoes"],
    queryFn: () => accountsPayableService.listExpenseApprovals(id as string),
    enabled: Boolean(id),
  });
}

export function useExpenseAllocationsQuery(id: string | undefined) {
  return useQuery({
    queryKey: ["accounts-payable", id, "rateios"],
    queryFn: () => accountsPayableService.listExpenseAllocations(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateAccountsPayableMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateAccountsPayableRequest) => accountsPayableService.createAccountsPayable(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["accounts-payable", "list"] }),
  });
}

function invalidate(queryClient: ReturnType<typeof useQueryClient>, id: string) {
  queryClient.invalidateQueries({ queryKey: ["accounts-payable", "list"] });
  queryClient.invalidateQueries({ queryKey: ["accounts-payable", id] });
  queryClient.invalidateQueries({ queryKey: ["accounts-payable", id, "aprovacoes"] });
  queryClient.invalidateQueries({ queryKey: ["accounts-payable", id, "rateios"] });
}

export function useUpdateAccountsPayableMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateAccountsPayableRequest }) =>
      accountsPayableService.updateAccountsPayable(id, body),
    onSuccess: (_data, { id }) => invalidate(queryClient, id),
  });
}

export function useDeleteAccountsPayableMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => accountsPayableService.deleteAccountsPayable(id),
    onSuccess: (_data, id) => invalidate(queryClient, id),
  });
}

export function useApproveAccountsPayableMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body?: ExpenseDecisionRequest }) =>
      accountsPayableService.approveAccountsPayable(id, body),
    onSuccess: (_data, { id }) => invalidate(queryClient, id),
  });
}

export function useRejectAccountsPayableMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: ExpenseDecisionRequest }) =>
      accountsPayableService.rejectAccountsPayable(id, body),
    onSuccess: (_data, { id }) => invalidate(queryClient, id),
  });
}

export function usePayAccountsPayableMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: PayAccountsPayableRequest }) =>
      accountsPayableService.payAccountsPayable(id, body),
    onSuccess: (_data, { id }) => invalidate(queryClient, id),
  });
}
