"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as mdfesService from "@/modules/documents/services/mdfes";
import type { CancelMdfeRequest, CreateMdfeRequest } from "@gestorfrete/types";

export function useMdfesQuery(params: mdfesService.ListMdfesParams) {
  return useQuery({
    queryKey: ["mdfes", "list", params],
    queryFn: () => mdfesService.listMdfes(params),
  });
}

export function useMdfeQuery(mdfeId: string | undefined) {
  return useQuery({
    queryKey: ["mdfes", mdfeId],
    queryFn: () => mdfesService.getMdfe(mdfeId as string),
    enabled: Boolean(mdfeId),
  });
}

export function useCreateMdfeMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateMdfeRequest) => mdfesService.createMdfe(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["mdfes", "list"] }),
  });
}

function invalidateMdfe(queryClient: ReturnType<typeof useQueryClient>, mdfeId: string) {
  queryClient.invalidateQueries({ queryKey: ["mdfes", "list"] });
  queryClient.invalidateQueries({ queryKey: ["mdfes", mdfeId] });
  queryClient.invalidateQueries({ queryKey: ["mdfes", mdfeId, "status-history"] });
}

export function useCloseMdfeMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (mdfeId: string) => mdfesService.closeMdfe(mdfeId),
    onSuccess: (_data, mdfeId) => invalidateMdfe(queryClient, mdfeId),
  });
}

export function useCancelMdfeMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ mdfeId, body }: { mdfeId: string; body: CancelMdfeRequest }) => mdfesService.cancelMdfe(mdfeId, body),
    onSuccess: (_data, { mdfeId }) => invalidateMdfe(queryClient, mdfeId),
  });
}
