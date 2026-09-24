"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import * as collectionService from "@/modules/freight/services/collection";
import type { RegisterCollectionRequest } from "@gestorfrete/types";

export function useRegisterCollectionMutation(tripId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: RegisterCollectionRequest) => collectionService.registerCollection(tripId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trips", "list"] });
      queryClient.invalidateQueries({ queryKey: ["trips", tripId] });
      queryClient.invalidateQueries({ queryKey: ["trips", tripId, "timeline"] });
    },
  });
}
