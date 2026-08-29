"use client";

import { useQuery } from "@tanstack/react-query";

import * as costApprovalsService from "@/modules/maintenance/services/cost-approvals";

export function useCostApprovalsQuery(workOrderId: string | undefined) {
  return useQuery({
    queryKey: ["work-orders", workOrderId, "cost-approvals"],
    queryFn: () => costApprovalsService.listCostApprovals(workOrderId as string),
    enabled: Boolean(workOrderId),
  });
}
