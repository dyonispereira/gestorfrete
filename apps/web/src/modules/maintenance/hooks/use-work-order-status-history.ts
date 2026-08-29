"use client";

import { useInfiniteQuery } from "@tanstack/react-query";

import * as workOrderStatusHistoryService from "@/modules/maintenance/services/work-order-status-history";

export function useWorkOrderStatusHistoryQuery(workOrderId: string | undefined) {
  return useInfiniteQuery({
    queryKey: ["work-orders", workOrderId, "status-history"],
    queryFn: ({ pageParam }: { pageParam: string | undefined }) =>
      workOrderStatusHistoryService.listWorkOrderStatusHistory(workOrderId as string, { cursor: pageParam }),
    enabled: Boolean(workOrderId),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => (lastPage.meta.pagination.has_more ? lastPage.meta.pagination.next_cursor : undefined),
  });
}
