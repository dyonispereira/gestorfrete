import { apiFetch } from "@/shared/lib/api-client";
import type {
  ApproveCostRequest,
  CancelWorkOrderRequest,
  CreateWorkOrderRequest,
  DiagnoseWorkOrderRequest,
  PaginatedResponse,
  RejectCostRequest,
  WorkOrder,
} from "@gestorfrete/types";

export interface ListWorkOrdersParams {
  page?: number;
  limit?: number;
  tractor_unit_id?: string;
  type?: string;
  status?: string;
}

function toQuery(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params) as [string, string | number | undefined][]) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export function listWorkOrders(params: ListWorkOrdersParams = {}): Promise<PaginatedResponse<WorkOrder>> {
  return apiFetch<PaginatedResponse<WorkOrder>>(`/ordens-servico${toQuery(params)}`);
}

export function getWorkOrder(id: string): Promise<WorkOrder> {
  return apiFetch<WorkOrder>(`/ordens-servico/${id}`);
}

export function createWorkOrder(body: CreateWorkOrderRequest): Promise<WorkOrder> {
  return apiFetch<WorkOrder>("/ordens-servico", { method: "POST", body });
}

export function diagnosticarWorkOrder(id: string, body: DiagnoseWorkOrderRequest): Promise<WorkOrder> {
  return apiFetch<WorkOrder>(`/ordens-servico/${id}/commands/diagnosticar`, { method: "POST", body });
}

export function submeterAprovacaoWorkOrder(id: string): Promise<WorkOrder> {
  return apiFetch<WorkOrder>(`/ordens-servico/${id}/commands/submeter-aprovacao`, { method: "POST" });
}

export function aprovarCustoWorkOrder(id: string, body: ApproveCostRequest = {}): Promise<WorkOrder> {
  return apiFetch<WorkOrder>(`/ordens-servico/${id}/commands/aprovar-custo`, { method: "POST", body });
}

export function reprovarCustoWorkOrder(id: string, body: RejectCostRequest): Promise<WorkOrder> {
  return apiFetch<WorkOrder>(`/ordens-servico/${id}/commands/reprovar-custo`, { method: "POST", body });
}

export function iniciarExecucaoWorkOrder(id: string): Promise<WorkOrder> {
  return apiFetch<WorkOrder>(`/ordens-servico/${id}/commands/iniciar-execucao`, { method: "POST" });
}

export function concluirWorkOrder(id: string): Promise<WorkOrder> {
  return apiFetch<WorkOrder>(`/ordens-servico/${id}/commands/concluir`, { method: "POST" });
}

export function fecharWorkOrder(id: string): Promise<WorkOrder> {
  return apiFetch<WorkOrder>(`/ordens-servico/${id}/commands/fechar`, { method: "POST" });
}

export function cancelarWorkOrder(id: string, body: CancelWorkOrderRequest): Promise<WorkOrder> {
  return apiFetch<WorkOrder>(`/ordens-servico/${id}/commands/cancelar`, { method: "POST", body });
}
