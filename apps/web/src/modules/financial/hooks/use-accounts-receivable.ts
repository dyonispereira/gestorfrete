"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as receivableService from "@/modules/financial/services/accounts-receivable";
import type { ConfirmReceiptRequest, CreateAccountsReceivableRequest, UpdateAccountsReceivableRequest } from "@gestorfrete/types";

export function useAccountsReceivableForInvoiceQuery(invoiceId: string | undefined) {
  return useQuery({
    queryKey: ["invoices", invoiceId, "contas-receber"],
    queryFn: () => receivableService.listAccountsReceivableForInvoice(invoiceId as string),
    enabled: Boolean(invoiceId),
  });
}

function invalidate(queryClient: ReturnType<typeof useQueryClient>, invoiceId: string) {
  queryClient.invalidateQueries({ queryKey: ["invoices", invoiceId, "contas-receber"] });
  queryClient.invalidateQueries({ queryKey: ["invoices", invoiceId] });
}

export function useCreateAccountsReceivableMutation(invoiceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateAccountsReceivableRequest) =>
      receivableService.createAccountsReceivable(invoiceId, body),
    onSuccess: () => invalidate(queryClient, invoiceId),
  });
}

export function useUpdateAccountsReceivableMutation(invoiceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateAccountsReceivableRequest }) =>
      receivableService.updateAccountsReceivable(invoiceId, id, body),
    onSuccess: () => invalidate(queryClient, invoiceId),
  });
}

export function useConfirmReceiptAccountsReceivableMutation(invoiceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: ConfirmReceiptRequest }) =>
      receivableService.confirmReceiptAccountsReceivable(invoiceId, id, body),
    onSuccess: () => invalidate(queryClient, invoiceId),
  });
}
