"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as suppliersService from "@/modules/maintenance/services/suppliers";
import type { CreateSupplierRequest, UpdateSupplierRequest } from "@gestorfrete/types";

export function useSuppliersQuery(params: suppliersService.ListSuppliersParams) {
  return useQuery({
    queryKey: ["suppliers", "list", params],
    queryFn: () => suppliersService.listSuppliers(params),
  });
}

export function useSupplierQuery(supplierId: string | undefined) {
  return useQuery({
    queryKey: ["suppliers", supplierId],
    queryFn: () => suppliersService.getSupplier(supplierId as string),
    enabled: Boolean(supplierId),
  });
}

export function useCreateSupplierMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateSupplierRequest) => suppliersService.createSupplier(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["suppliers", "list"] }),
  });
}

export function useUpdateSupplierMutation(supplierId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: UpdateSupplierRequest) => suppliersService.updateSupplier(supplierId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["suppliers", "list"] });
      queryClient.invalidateQueries({ queryKey: ["suppliers", supplierId] });
    },
  });
}

export function useDeleteSupplierMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (supplierId: string) => suppliersService.deleteSupplier(supplierId),
    onSuccess: (_data, supplierId) => {
      queryClient.invalidateQueries({ queryKey: ["suppliers", "list"] });
      queryClient.invalidateQueries({ queryKey: ["suppliers", supplierId] });
    },
  });
}
