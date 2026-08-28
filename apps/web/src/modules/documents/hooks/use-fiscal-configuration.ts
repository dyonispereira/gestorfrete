"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as fiscalConfigurationService from "@/modules/documents/services/fiscal-configuration";
import type { UpdateFiscalConfigurationRequest } from "@gestorfrete/types";

export function useFiscalConfigurationQuery() {
  return useQuery({
    queryKey: ["fiscal-configuration"],
    queryFn: () => fiscalConfigurationService.getFiscalConfiguration(),
  });
}

export function useUpdateFiscalConfigurationMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: UpdateFiscalConfigurationRequest) => fiscalConfigurationService.updateFiscalConfiguration(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["fiscal-configuration"] }),
  });
}
