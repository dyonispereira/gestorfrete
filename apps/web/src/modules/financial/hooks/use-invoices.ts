"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as invoicesService from "@/modules/financial/services/invoices";
import type { CreateInvoiceRequest } from "@gestorfrete/types";

export function useInvoicesListQuery(params: invoicesService.ListInvoicesParams) {
  return useQuery({
    queryKey: ["invoices", "list", params],
    queryFn: () => invoicesService.listInvoices(params),
  });
}

export function useInvoiceQuery(id: string | undefined) {
  return useQuery({
    queryKey: ["invoices", id],
    queryFn: () => invoicesService.getInvoice(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateInvoiceMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateInvoiceRequest) => invoicesService.createInvoice(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["invoices", "list"] }),
  });
}

export function useCancelInvoiceMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => invoicesService.cancelInvoice(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ["invoices", "list"] });
      queryClient.invalidateQueries({ queryKey: ["invoices", id] });
    },
  });
}
