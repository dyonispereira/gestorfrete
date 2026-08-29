import { apiFetch } from "@/shared/lib/api-client";
import type { CreateWorkOrderItemRequest, PaginatedResponse, WorkOrderItem } from "@gestorfrete/types";

export function listWorkOrderItems(workOrderId: string): Promise<PaginatedResponse<WorkOrderItem>> {
  return apiFetch<PaginatedResponse<WorkOrderItem>>(`/ordens-servico/${workOrderId}/itens`);
}

/** Bloqueado pelo Backend depois de CONCLUIDA/FECHADA/CANCELADA — sem gate extra aqui, o erro real já explica. */
export function createWorkOrderItem(workOrderId: string, body: CreateWorkOrderItemRequest): Promise<WorkOrderItem> {
  return apiFetch<WorkOrderItem>(`/ordens-servico/${workOrderId}/itens`, { method: "POST", body });
}
