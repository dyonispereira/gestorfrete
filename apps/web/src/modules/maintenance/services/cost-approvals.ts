import { apiFetch } from "@/shared/lib/api-client";
import type { CostApproval, PaginatedResponse } from "@gestorfrete/types";

export function listCostApprovals(workOrderId: string): Promise<PaginatedResponse<CostApproval>> {
  return apiFetch<PaginatedResponse<CostApproval>>(`/ordens-servico/${workOrderId}/aprovacoes-custo`);
}
