"use client";

import * as React from "react";
import { Plus, Wrench } from "lucide-react";

import { Button, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { WorkOrderStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useWorkOrdersQuery } from "@/modules/maintenance/hooks/use-work-orders";
import { WorkOrderFormDrawer } from "@/modules/maintenance/components/work-order-form-drawer";
import { WorkOrdersTable } from "@/modules/maintenance/components/work-orders-table";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const STATUS_OPTIONS: Array<{ value: "all" | WorkOrderStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "ABERTA", label: "Aberta" },
  { value: "EM_DIAGNOSTICO", label: "Em diagnóstico" },
  { value: "AGUARDANDO_APROVACAO", label: "Aguardando aprovação" },
  { value: "EM_EXECUCAO", label: "Em execução" },
  { value: "CONCLUIDA", label: "Concluída" },
  { value: "FECHADA", label: "Fechada" },
  { value: "CANCELADA", label: "Cancelada" },
];

export default function WorkOrdersPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [status, setStatus] = React.useState<"all" | WorkOrderStatus>("all");
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const workOrdersQuery = useWorkOrdersQuery({ page, limit: 20, status: status === "all" ? undefined : status });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Ordens de Serviço</h1>
          <p className="text-sm text-muted-foreground">Diagnóstico, aprovação de custo e execução de manutenção.</p>
        </div>
        {hasPermission("maintenance.work_order.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Nova ordem de serviço
          </Button>
        ) : null}
      </div>

      <Select
        value={status}
        onValueChange={(value) => {
          setStatus(value as "all" | WorkOrderStatus);
          setPage(1);
        }}
      >
        <SelectTrigger className="sm:w-56">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {STATUS_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {workOrdersQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : workOrdersQuery.error ? (
        <ErrorState
          title="Não foi possível carregar as ordens de serviço"
          description={workOrdersQuery.error instanceof Error ? workOrdersQuery.error.message : undefined}
          onRetry={() => workOrdersQuery.refetch()}
        />
      ) : workOrdersQuery.data && workOrdersQuery.data.data.length > 0 ? (
        <>
          <WorkOrdersTable workOrders={workOrdersQuery.data.data} />
          <Pagination
            page={workOrdersQuery.data.meta.pagination.page}
            limit={workOrdersQuery.data.meta.pagination.limit}
            total={workOrdersQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={Wrench} title="Nenhuma ordem de serviço encontrada" description="Ajuste o filtro ou crie a primeira ordem de serviço." />
      )}

      <WorkOrderFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}
