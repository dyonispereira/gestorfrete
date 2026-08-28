"use client";

import { useInfiniteQuery } from "@tanstack/react-query";

import * as mdfeStatusHistoryService from "@/modules/documents/services/mdfe-status-history";

export function useMdfeStatusHistoryQuery(mdfeId: string | undefined) {
  return useInfiniteQuery({
    queryKey: ["mdfes", mdfeId, "status-history"],
    queryFn: ({ pageParam }: { pageParam: string | undefined }) =>
      mdfeStatusHistoryService.listMdfeStatusHistory(mdfeId as string, { cursor: pageParam }),
    enabled: Boolean(mdfeId),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => (lastPage.meta.pagination.has_more ? lastPage.meta.pagination.next_cursor : undefined),
  });
}
