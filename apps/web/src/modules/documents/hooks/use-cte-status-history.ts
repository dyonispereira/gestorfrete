"use client";

import { useInfiniteQuery } from "@tanstack/react-query";

import * as cteStatusHistoryService from "@/modules/documents/services/cte-status-history";

export function useCteStatusHistoryQuery(cteId: string | undefined) {
  return useInfiniteQuery({
    queryKey: ["ctes", cteId, "status-history"],
    queryFn: ({ pageParam }: { pageParam: string | undefined }) =>
      cteStatusHistoryService.listCteStatusHistory(cteId as string, { cursor: pageParam }),
    enabled: Boolean(cteId),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => (lastPage.meta.pagination.has_more ? lastPage.meta.pagination.next_cursor : undefined),
  });
}
