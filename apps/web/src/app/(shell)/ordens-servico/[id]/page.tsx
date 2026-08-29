"use client";

import { useParams } from "next/navigation";

import { Card, CardContent, CardDescription, CardHeader, CardTitle, Tabs, TabsContent, TabsList, TabsTrigger } from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useWorkOrderQuery } from "@/modules/maintenance/hooks/use-work-orders";
import { ChecklistPanel } from "@/modules/maintenance/components/checklist-panel";
import { CostApprovalsTab } from "@/modules/maintenance/components/cost-approvals-tab";
import { WorkOrderCommandsPanel } from "@/modules/maintenance/components/work-order-commands-panel";
import { WorkOrderItemsTab } from "@/modules/maintenance/components/work-order-items-tab";
import { WorkOrderStatusBadge } from "@/modules/maintenance/components/work-order-status-badge";
import { WorkOrderStatusHistory } from "@/modules/maintenance/components/work-order-status-history";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";
import { useBreadcrumbLabel } from "@/shared/components/shell/breadcrumb-label-context";

function formatMoney(value: string | undefined): string {
  if (value === undefined) return "—";
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export default function WorkOrderDetailPage() {
  const params = useParams<{ id: string }>();
  const workOrderId = params.id;
  const { hasPermission } = usePermissions();

  const workOrderQuery = useWorkOrderQuery(workOrderId);
  const workOrder = workOrderQuery.data;
  useBreadcrumbLabel(`/ordens-servico/${workOrderId}`, workOrder?.codigo);

  if (workOrderQuery.isLoading) return <LoadingState rows={6} />;
  if (workOrderQuery.error || !workOrder)
    return (
      <ErrorState
        title="Não foi possível carregar a ordem de serviço"
        description={workOrderQuery.error instanceof Error ? workOrderQuery.error.message : undefined}
        onRetry={() => workOrderQuery.refetch()}
      />
    );

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">{workOrder.codigo}</h1>
        <div className="mt-2">
          <WorkOrderStatusBadge status={workOrder.status} />
        </div>
      </div>

      <WorkOrderCommandsPanel workOrder={workOrder} />

      <Tabs defaultValue="visao-geral">
        <TabsList>
          <TabsTrigger value="visao-geral">Visão Geral</TabsTrigger>
          <TabsTrigger value="itens">Itens</TabsTrigger>
          <TabsTrigger value="aprovacoes">Aprovações de Custo</TabsTrigger>
          <TabsTrigger value="checklist">Checklist</TabsTrigger>
          <TabsTrigger value="historico">Histórico</TabsTrigger>
        </TabsList>

        <TabsContent value="visao-geral">
          <Card>
            <CardHeader>
              <CardTitle>Dados da ordem de serviço</CardTitle>
              <CardDescription>Origem: {workOrder.opening_origin}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-2 text-sm">
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Veículo</span>
                <span className="font-medium">{workOrder.tractor_unit_id}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Problema relatado</span>
                <span className="font-medium">{workOrder.problem_description}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Diagnóstico técnico</span>
                <span className="font-medium">{workOrder.technical_diagnosis ?? "—"}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Causa</span>
                <span className="font-medium">{workOrder.cause ?? "—"}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Custo previsto</span>
                <span className="font-medium">{formatMoney(workOrder.predicted_cost)}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Custo realizado</span>
                <span className="font-medium">{formatMoney(workOrder.actual_cost)}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Início da execução</span>
                <span className="font-medium">
                  {workOrder.execution_started_at ? new Date(workOrder.execution_started_at).toLocaleString("pt-BR") : "—"}
                </span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Conclusão</span>
                <span className="font-medium">
                  {workOrder.completed_at ? new Date(workOrder.completed_at).toLocaleString("pt-BR") : "—"}
                </span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="itens">
          <WorkOrderItemsTab workOrderId={workOrderId} canCreate={hasPermission("maintenance.work_order_item.create")} />
        </TabsContent>

        <TabsContent value="aprovacoes">
          <CostApprovalsTab workOrderId={workOrderId} />
        </TabsContent>

        <TabsContent value="checklist">
          <ChecklistPanel
            referenceType="ORDEM_SERVICO"
            referenceId={workOrderId}
            canFill={hasPermission("maintenance.checklist.fill")}
            canApprove={hasPermission("maintenance.checklist.approve")}
            canReject={hasPermission("maintenance.checklist.reject")}
          />
        </TabsContent>

        <TabsContent value="historico">
          <WorkOrderStatusHistory workOrderId={workOrderId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
