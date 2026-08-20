import { apiFetch } from "@/shared/lib/api-client";
import type { Contact, CreateContactRequest, PaginatedResponse, UpdateContactRequest } from "@gestorfrete/types";

/** Exclusive to Cliente (`contatos_cliente.cliente_id` FK) — no equivalent for other Cadastros entities. */
export function listClientContacts(clientId: string): Promise<PaginatedResponse<Contact>> {
  return apiFetch<PaginatedResponse<Contact>>(`/clients/${clientId}/contacts`);
}

export function createClientContact(clientId: string, body: CreateContactRequest): Promise<Contact> {
  return apiFetch<Contact>(`/clients/${clientId}/contacts`, { method: "POST", body });
}

export function updateClientContact(clientId: string, contactId: string, body: UpdateContactRequest): Promise<Contact> {
  return apiFetch<Contact>(`/clients/${clientId}/contacts/${contactId}`, { method: "PATCH", body });
}

export function deleteClientContact(clientId: string, contactId: string): Promise<void> {
  return apiFetch<void>(`/clients/${clientId}/contacts/${contactId}`, { method: "DELETE" });
}
