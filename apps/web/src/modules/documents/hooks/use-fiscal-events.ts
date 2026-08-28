"use client";

import { useInfiniteQuery } from "@tanstack/react-query";

import * as fiscalEventsService from "@/modules/documents/services/fiscal-events";

export function useFiscalEventsQuery(filters: Omit<fiscalEventsService.ListFiscalEventsParams, "cursor"> = {}) {
  return useInfiniteQuery({
    queryKey: ["fiscal-events", filters],
    queryFn: ({ pageParam }: { pageParam: string | undefined }) =>
      fiscalEventsService.listFiscalEvents({ ...filters, cursor: pageParam }),
    enabled: true,
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => (lastPage.meta.pagination.has_more ? lastPage.meta.pagination.next_cursor : undefined),
  });
}
