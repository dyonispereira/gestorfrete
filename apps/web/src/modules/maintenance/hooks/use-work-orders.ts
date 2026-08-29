"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as workOrdersService from "@/modules/maintenance/services/work-orders";
import type {
  ApproveCostRequest,
  CancelWorkOrderRequest,
  ConcludeWorkOrderRequest,
  CreateWorkOrderRequest,
  DiagnoseWorkOrderRequest,
  RejectCostRequest,
} from "@gestorfrete/types";

export function useWorkOrdersQuery(params: workOrdersService.ListWorkOrdersParams) {
  return useQuery({
    queryKey: ["work-orders", "list", params],
    queryFn: () => workOrdersService.listWorkOrders(params),
  });
}

export function useWorkOrderQuery(workOrderId: string | undefined) {
  return useQuery({
    queryKey: ["work-orders", workOrderId],
    queryFn: () => workOrdersService.getWorkOrder(workOrderId as string),
    enabled: Boolean(workOrderId),
  });
}

export function useCreateWorkOrderMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateWorkOrderRequest) => workOrdersService.createWorkOrder(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["work-orders", "list"] }),
  });
}

function invalidateWorkOrder(queryClient: ReturnType<typeof useQueryClient>, workOrderId: string) {
  queryClient.invalidateQueries({ queryKey: ["work-orders", "list"] });
  queryClient.invalidateQueries({ queryKey: ["work-orders", workOrderId] });
  queryClient.invalidateQueries({ queryKey: ["work-orders", workOrderId, "status-history"] });
  queryClient.invalidateQueries({ queryKey: ["work-orders", workOrderId, "cost-approvals"] });
}

export function useDiagnosticarWorkOrderMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ workOrderId, body }: { workOrderId: string; body: DiagnoseWorkOrderRequest }) =>
      workOrdersService.diagnosticarWorkOrder(workOrderId, body),
    onSuccess: (_data, { workOrderId }) => invalidateWorkOrder(queryClient, workOrderId),
  });
}

export function useSubmeterAprovacaoWorkOrderMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (workOrderId: string) => workOrdersService.submeterAprovacaoWorkOrder(workOrderId),
    onSuccess: (_data, workOrderId) => invalidateWorkOrder(queryClient, workOrderId),
  });
}

export function useAprovarCustoWorkOrderMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ workOrderId, body }: { workOrderId: string; body?: ApproveCostRequest }) =>
      workOrdersService.aprovarCustoWorkOrder(workOrderId, body),
    onSuccess: (_data, { workOrderId }) => invalidateWorkOrder(queryClient, workOrderId),
  });
}

export function useReprovarCustoWorkOrderMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ workOrderId, body }: { workOrderId: string; body: RejectCostRequest }) =>
      workOrdersService.reprovarCustoWorkOrder(workOrderId, body),
    onSuccess: (_data, { workOrderId }) => invalidateWorkOrder(queryClient, workOrderId),
  });
}

export function useIniciarExecucaoWorkOrderMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (workOrderId: string) => workOrdersService.iniciarExecucaoWorkOrder(workOrderId),
    onSuccess: (_data, workOrderId) => invalidateWorkOrder(queryClient, workOrderId),
  });
}

export function useConcluirWorkOrderMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ workOrderId, body }: { workOrderId: string; body?: ConcludeWorkOrderRequest }) =>
      workOrdersService.concluirWorkOrder(workOrderId, body),
    onSuccess: (_data, { workOrderId }) => invalidateWorkOrder(queryClient, workOrderId),
  });
}

export function useFecharWorkOrderMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (workOrderId: string) => workOrdersService.fecharWorkOrder(workOrderId),
    onSuccess: (_data, workOrderId) => invalidateWorkOrder(queryClient, workOrderId),
  });
}

export function useCancelarWorkOrderMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ workOrderId, body }: { workOrderId: string; body: CancelWorkOrderRequest }) =>
      workOrdersService.cancelarWorkOrder(workOrderId, body),
    onSuccess: (_data, { workOrderId }) => invalidateWorkOrder(queryClient, workOrderId),
  });
}
