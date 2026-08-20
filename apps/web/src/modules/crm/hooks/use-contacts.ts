"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as contactsService from "@/modules/crm/services/contacts";
import type { CreateContactRequest, UpdateContactRequest } from "@gestorfrete/types";

export function useClientContactsQuery(clientId: string | undefined) {
  return useQuery({
    queryKey: ["clients", clientId, "contacts"],
    queryFn: () => contactsService.listClientContacts(clientId as string),
    enabled: Boolean(clientId),
  });
}

function useInvalidateContacts(clientId: string) {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: ["clients", clientId, "contacts"] });
}

export function useCreateClientContactMutation(clientId: string) {
  const invalidate = useInvalidateContacts(clientId);
  return useMutation({
    mutationFn: (body: CreateContactRequest) => contactsService.createClientContact(clientId, body),
    onSuccess: invalidate,
  });
}

export function useUpdateClientContactMutation(clientId: string) {
  const invalidate = useInvalidateContacts(clientId);
  return useMutation({
    mutationFn: ({ contactId, body }: { contactId: string; body: UpdateContactRequest }) =>
      contactsService.updateClientContact(clientId, contactId, body),
    onSuccess: invalidate,
  });
}

export function useDeleteClientContactMutation(clientId: string) {
  const invalidate = useInvalidateContacts(clientId);
  return useMutation({
    mutationFn: (contactId: string) => contactsService.deleteClientContact(clientId, contactId),
    onSuccess: invalidate,
  });
}
