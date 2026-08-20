"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as implementsService from "@/modules/fleet/services/implements";
import type { CreateImplementRequest, UpdateImplementRequest } from "@gestorfrete/types";

export function useImplementsQuery(params: implementsService.ListImplementsParams) {
  return useQuery({
    queryKey: ["implements", "list", params],
    queryFn: () => implementsService.listImplements(params),
  });
}

export function useImplementQuery(implementId: string | undefined) {
  return useQuery({
    queryKey: ["implements", implementId],
    queryFn: () => implementsService.getImplement(implementId as string),
    enabled: Boolean(implementId),
  });
}

export function useCreateImplementMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateImplementRequest) => implementsService.createImplement(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["implements", "list"] }),
  });
}

export function useUpdateImplementMutation(implementId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: UpdateImplementRequest) => implementsService.updateImplement(implementId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["implements", "list"] });
      queryClient.invalidateQueries({ queryKey: ["implements", implementId] });
    },
  });
}

export function useDeleteImplementMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (implementId: string) => implementsService.deleteImplement(implementId),
    onSuccess: (_data, implementId) => {
      queryClient.invalidateQueries({ queryKey: ["implements", "list"] });
      queryClient.invalidateQueries({ queryKey: ["implements", implementId] });
    },
  });
}
