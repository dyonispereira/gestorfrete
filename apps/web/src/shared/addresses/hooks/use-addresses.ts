"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as addressesService from "@/shared/addresses/services/addresses";
import type { AddressOwnerBasePath } from "@/shared/addresses/services/addresses";
import type { CreateAddressRequest, UpdateAddressRequest } from "@gestorfrete/types";

export function useAddressesQuery(ownerBasePath: AddressOwnerBasePath, ownerId: string | undefined) {
  return useQuery({
    queryKey: ["addresses", ownerBasePath, ownerId],
    queryFn: () => addressesService.listAddresses(ownerBasePath, ownerId as string),
    enabled: Boolean(ownerId),
  });
}

function useInvalidateAddresses(ownerBasePath: AddressOwnerBasePath, ownerId: string) {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: ["addresses", ownerBasePath, ownerId] });
}

export function useCreateAddressMutation(ownerBasePath: AddressOwnerBasePath, ownerId: string) {
  const invalidate = useInvalidateAddresses(ownerBasePath, ownerId);
  return useMutation({
    mutationFn: (body: CreateAddressRequest) => addressesService.createAddress(ownerBasePath, ownerId, body),
    onSuccess: invalidate,
  });
}

export function useUpdateAddressMutation(ownerBasePath: AddressOwnerBasePath, ownerId: string) {
  const invalidate = useInvalidateAddresses(ownerBasePath, ownerId);
  return useMutation({
    mutationFn: ({ addressId, body }: { addressId: string; body: UpdateAddressRequest }) =>
      addressesService.updateAddress(ownerBasePath, ownerId, addressId, body),
    onSuccess: invalidate,
  });
}

export function useDeleteAddressMutation(ownerBasePath: AddressOwnerBasePath, ownerId: string) {
  const invalidate = useInvalidateAddresses(ownerBasePath, ownerId);
  return useMutation({
    mutationFn: (addressId: string) => addressesService.deleteAddress(ownerBasePath, ownerId, addressId),
    onSuccess: invalidate,
  });
}
