import { apiFetch } from "@/shared/lib/api-client";
import type { Address, CreateAddressRequest, PaginatedResponse, UpdateAddressRequest } from "@gestorfrete/types";

/** `"clients"` or `"suppliers"` — the owner's real REST path segment (`client_router.py`/`supplier_router.py`). */
export type AddressOwnerBasePath = "clients" | "suppliers";

/** List never really paginates (the Backend always returns every row and fakes `page:1`) — see Lote Cadastros plan. */
export function listAddresses(ownerBasePath: AddressOwnerBasePath, ownerId: string): Promise<PaginatedResponse<Address>> {
  return apiFetch<PaginatedResponse<Address>>(`/${ownerBasePath}/${ownerId}/addresses`);
}

export function createAddress(
  ownerBasePath: AddressOwnerBasePath,
  ownerId: string,
  body: CreateAddressRequest
): Promise<Address> {
  return apiFetch<Address>(`/${ownerBasePath}/${ownerId}/addresses`, { method: "POST", body });
}

export function updateAddress(
  ownerBasePath: AddressOwnerBasePath,
  ownerId: string,
  addressId: string,
  body: UpdateAddressRequest
): Promise<Address> {
  return apiFetch<Address>(`/${ownerBasePath}/${ownerId}/addresses/${addressId}`, { method: "PATCH", body });
}

export function deleteAddress(ownerBasePath: AddressOwnerBasePath, ownerId: string, addressId: string): Promise<void> {
  return apiFetch<void>(`/${ownerBasePath}/${ownerId}/addresses/${addressId}`, { method: "DELETE" });
}
