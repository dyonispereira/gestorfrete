"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as clientsService from "@/modules/crm/services/clients";
import type { CreateClientRequest, UpdateClientRequest } from "@gestorfrete/types";

export function useClientsQuery(params: clientsService.ListClientsParams) {
  return useQuery({
    queryKey: ["clients", "list", params],
    queryFn: () => clientsService.listClients(params),
  });
}

export function useClientQuery(clientId: string | undefined) {
  return useQuery({
    queryKey: ["clients", clientId],
    queryFn: () => clientsService.getClient(clientId as string),
    enabled: Boolean(clientId),
  });
}

export function useCreateClientMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateClientRequest) => clientsService.createClient(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["clients", "list"] }),
  });
}

export function useUpdateClientMutation(clientId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: UpdateClientRequest) => clientsService.updateClient(clientId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clients", "list"] });
      queryClient.invalidateQueries({ queryKey: ["clients", clientId] });
    },
  });
}

export function useDeactivateClientMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (clientId: string) => clientsService.deactivateClient(clientId),
    onSuccess: (_data, clientId) => {
      queryClient.invalidateQueries({ queryKey: ["clients", "list"] });
      queryClient.invalidateQueries({ queryKey: ["clients", clientId] });
    },
  });
}
