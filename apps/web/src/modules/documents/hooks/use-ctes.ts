"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as ctesService from "@/modules/documents/services/ctes";
import type { CancelCteRequest } from "@gestorfrete/types";

export function useCtesQuery(params: ctesService.ListCtesParams) {
  return useQuery({
    queryKey: ["ctes", "list", params],
    queryFn: () => ctesService.listCtes(params),
  });
}

export function useCteQuery(cteId: string | undefined) {
  return useQuery({
    queryKey: ["ctes", cteId],
    queryFn: () => ctesService.getCte(cteId as string),
    enabled: Boolean(cteId),
  });
}

function invalidateCte(queryClient: ReturnType<typeof useQueryClient>, cteId: string) {
  queryClient.invalidateQueries({ queryKey: ["ctes", "list"] });
  queryClient.invalidateQueries({ queryKey: ["ctes", cteId] });
  queryClient.invalidateQueries({ queryKey: ["ctes", cteId, "status-history"] });
}

function useCteCommandMutation(mutationFn: (cteId: string) => Promise<unknown>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (cteId: string) => mutationFn(cteId),
    onSuccess: (_data, cteId) => invalidateCte(queryClient, cteId),
  });
}

export function useValidateCteMutation() {
  return useCteCommandMutation(ctesService.validateCte);
}

export function useSignCteMutation() {
  return useCteCommandMutation(ctesService.signCte);
}

export function useTransmitCteMutation() {
  return useCteCommandMutation(ctesService.transmitCte);
}

export function useInutilizeCteMutation() {
  return useCteCommandMutation(ctesService.inutilizeCte);
}

export function useCancelCteMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ cteId, body }: { cteId: string; body: CancelCteRequest }) => ctesService.cancelCte(cteId, body),
    onSuccess: (_data, { cteId }) => invalidateCte(queryClient, cteId),
  });
}
