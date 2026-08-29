"use client";

import { useInfiniteQuery } from "@tanstack/react-query";

import * as checklistStatusHistoryService from "@/modules/maintenance/services/checklist-status-history";

export function useChecklistStatusHistoryQuery(checklistId: string | undefined) {
  return useInfiniteQuery({
    queryKey: ["checklists", checklistId, "status-history"],
    queryFn: ({ pageParam }: { pageParam: string | undefined }) =>
      checklistStatusHistoryService.listChecklistStatusHistory(checklistId as string, { cursor: pageParam }),
    enabled: Boolean(checklistId),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => (lastPage.meta.pagination.has_more ? lastPage.meta.pagination.next_cursor : undefined),
  });
}
