"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as receivableService from "@/modules/financial/services/accounts-receivable";
import type {
  ConfirmReceiptRequest,
  CreateAccountsReceivableRequest,
  UpdateAccountsReceivableRequest,
} from "@gestorfrete/types";
import type { ListAccountsReceivableGlobalParams } from "@/modules/financial/services/accounts-receivable";

export function useAccountsReceivableForInvoiceQuery(invoiceId: string | undefined) {
  return useQuery({
    queryKey: ["invoices", invoiceId, "contas-receber"],
    queryFn: () => receivableService.listAccountsReceivableForInvoice(invoiceId as string),
    enabled: Boolean(invoiceId),
  });
}

/** Consulta agregada entre Faturas (Lote Financeiro, Parte 2.1) — `GET /contas-receber`. */
export function useAccountsReceivableGlobalListQuery(params: ListAccountsReceivableGlobalParams) {
  return useQuery({
    queryKey: ["contas-receber-global", params],
    queryFn: () => receivableService.listAccountsReceivableGlobal(params),
  });
}

function invalidate(queryClient: ReturnType<typeof useQueryClient>, invoiceId: string) {
  queryClient.invalidateQueries({ queryKey: ["invoices", invoiceId, "contas-receber"] });
  queryClient.invalidateQueries({ queryKey: ["invoices", invoiceId] });
  queryClient.invalidateQueries({ queryKey: ["contas-receber-global"] });
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
