"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as priceTablesService from "@/modules/pricing/services/price-tables";
import type { CreatePriceTableItemRequest, CreatePriceTableRequest, UpdatePriceTableRequest } from "@gestorfrete/types";

export function usePriceTablesQuery(params: priceTablesService.ListPriceTablesParams) {
  return useQuery({
    queryKey: ["price-tables", "list", params],
    queryFn: () => priceTablesService.listPriceTables(params),
  });
}

export function usePriceTableQuery(priceTableId: string | undefined) {
  return useQuery({
    queryKey: ["price-tables", priceTableId],
    queryFn: () => priceTablesService.getPriceTable(priceTableId as string),
    enabled: Boolean(priceTableId),
  });
}

export function usePriceTableItemsQuery(priceTableId: string | undefined) {
  return useQuery({
    queryKey: ["price-tables", priceTableId, "items"],
    queryFn: () => priceTablesService.listPriceTableItems(priceTableId as string),
    enabled: Boolean(priceTableId),
  });
}

export function useCreatePriceTableMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreatePriceTableRequest) => priceTablesService.createPriceTable(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["price-tables", "list"] }),
  });
}

export function useUpdatePriceTableMutation(priceTableId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: UpdatePriceTableRequest) => priceTablesService.updatePriceTable(priceTableId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["price-tables", "list"] });
      queryClient.invalidateQueries({ queryKey: ["price-tables", priceTableId] });
    },
  });
}

function usePriceTableStatusMutation(mutationFn: (priceTableId: string) => Promise<unknown>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (priceTableId: string) => mutationFn(priceTableId),
    onSuccess: (_data, priceTableId) => {
      queryClient.invalidateQueries({ queryKey: ["price-tables", "list"] });
      queryClient.invalidateQueries({ queryKey: ["price-tables", priceTableId] });
    },
  });
}

export function useActivatePriceTableMutation() {
  return usePriceTableStatusMutation((priceTableId) => priceTablesService.activatePriceTable(priceTableId));
}

export function useExpirePriceTableMutation() {
  return usePriceTableStatusMutation((priceTableId) => priceTablesService.expirePriceTable(priceTableId));
}

export function useCreatePriceTableItemMutation(priceTableId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreatePriceTableItemRequest) => priceTablesService.createPriceTableItem(priceTableId, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["price-tables", priceTableId, "items"] }),
  });
}

export function useDeletePriceTableItemMutation(priceTableId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => priceTablesService.deletePriceTableItem(priceTableId, itemId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["price-tables", priceTableId, "items"] }),
  });
}
