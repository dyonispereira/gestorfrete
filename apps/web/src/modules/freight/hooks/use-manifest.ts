"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import * as manifestService from "@/modules/freight/services/manifest";
import type { ConfirmManifestRequest } from "@gestorfrete/types";

export function useConfirmManifestMutation(tripId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ConfirmManifestRequest) => manifestService.confirmManifest(tripId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trips", "list"] });
      queryClient.invalidateQueries({ queryKey: ["trips", tripId] });
      queryClient.invalidateQueries({ queryKey: ["trips", tripId, "timeline"] });
    },
  });
}
