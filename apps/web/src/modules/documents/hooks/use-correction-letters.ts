"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as correctionLettersService from "@/modules/documents/services/correction-letters";
import type { CreateCorrectionLetterRequest } from "@gestorfrete/types";

export function useCorrectionLettersQuery(cteId: string | undefined) {
  return useQuery({
    queryKey: ["ctes", cteId, "correction-letters"],
    queryFn: () => correctionLettersService.listCorrectionLetters(cteId as string),
    enabled: Boolean(cteId),
  });
}

export function useCreateCorrectionLetterMutation(cteId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateCorrectionLetterRequest) => correctionLettersService.createCorrectionLetter(cteId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ctes", cteId, "correction-letters"] });
      queryClient.invalidateQueries({ queryKey: ["ctes", cteId, "status-history"] });
    },
  });
}
