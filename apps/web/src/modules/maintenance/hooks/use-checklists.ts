"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as checklistsService from "@/modules/maintenance/services/checklists";
import type { CreateChecklistRequest, RejectChecklistRequest, SubmitChecklistRequest } from "@gestorfrete/types";

export function useChecklistsQuery(params: checklistsService.ListChecklistsParams) {
  return useQuery({
    queryKey: ["checklists", "list", params],
    queryFn: () => checklistsService.listChecklists(params),
  });
}

export function useChecklistQuery(checklistId: string | undefined) {
  return useQuery({
    queryKey: ["checklists", checklistId],
    queryFn: () => checklistsService.getChecklist(checklistId as string),
    enabled: Boolean(checklistId),
  });
}

function invalidateChecklists(queryClient: ReturnType<typeof useQueryClient>, checklistId?: string) {
  queryClient.invalidateQueries({ queryKey: ["checklists", "list"] });
  if (checklistId) {
    queryClient.invalidateQueries({ queryKey: ["checklists", checklistId] });
    queryClient.invalidateQueries({ queryKey: ["checklists", checklistId, "status-history"] });
  }
  // A viagem referenciada muda de status como efeito colateral (D376) — invalida a viagem também.
  queryClient.invalidateQueries({ queryKey: ["trips"] });
}

export function useCreateChecklistMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateChecklistRequest) => checklistsService.createChecklist(body),
    onSuccess: () => invalidateChecklists(queryClient),
  });
}

export function useStartChecklistMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (checklistId: string) => checklistsService.startChecklist(checklistId),
    onSuccess: (_data, checklistId) => invalidateChecklists(queryClient, checklistId),
  });
}

export function useSubmitChecklistMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ checklistId, body }: { checklistId: string; body: SubmitChecklistRequest }) =>
      checklistsService.submitChecklist(checklistId, body),
    onSuccess: (_data, { checklistId }) => invalidateChecklists(queryClient, checklistId),
  });
}

export function useApproveChecklistMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (checklistId: string) => checklistsService.approveChecklist(checklistId),
    onSuccess: (_data, checklistId) => invalidateChecklists(queryClient, checklistId),
  });
}

export function useRejectChecklistMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ checklistId, body }: { checklistId: string; body: RejectChecklistRequest }) =>
      checklistsService.rejectChecklist(checklistId, body),
    onSuccess: (_data, { checklistId }) => invalidateChecklists(queryClient, checklistId),
  });
}
