"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as referencedNfesService from "@/modules/documents/services/referenced-nfes";
import type { CreateReferencedNfeRequest } from "@gestorfrete/types";

export function useReferencedNfesQuery(cteId: string | undefined) {
  return useQuery({
    queryKey: ["ctes", cteId, "referenced-nfes"],
    queryFn: () => referencedNfesService.listReferencedNfes(cteId as string),
    enabled: Boolean(cteId),
  });
}

export function useCreateReferencedNfeMutation(cteId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateReferencedNfeRequest) => referencedNfesService.createReferencedNfe(cteId, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ctes", cteId, "referenced-nfes"] }),
  });
}
