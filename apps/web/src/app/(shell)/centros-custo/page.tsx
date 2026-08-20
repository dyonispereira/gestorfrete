"use client";

import * as React from "react";
import { Banknote, Plus } from "lucide-react";

import { Button, Input, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { CostCenterStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useCostCentersQuery } from "@/modules/financial/hooks/use-cost-centers";
import { CostCentersTable } from "@/modules/financial/components/cost-centers-table";
import { CostCenterFormDrawer } from "@/modules/financial/components/cost-center-form-drawer";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const STATUS_OPTIONS: Array<{ value: "all" | CostCenterStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "ATIVO", label: "Ativo" },
  { value: "INATIVO", label: "Inativo" },
];

export default function CostCentersPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [status, setStatus] = React.useState<"all" | CostCenterStatus>("all");
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const costCentersQuery = useCostCentersQuery({ page, limit: 20, search, status: status === "all" ? undefined : status });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Centros de Custo</h1>
          <p className="text-sm text-muted-foreground">Centros de custo do tenant.</p>
        </div>
        {hasPermission("financial.cost_center.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Novo centro de custo
          </Button>
        ) : null}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          placeholder="Buscar por nome…"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPage(1);
          }}
          className="sm:max-w-xs"
        />
        <Select
          value={status}
          onValueChange={(value) => {
            setStatus(value as "all" | CostCenterStatus);
            setPage(1);
          }}
        >
          <SelectTrigger className="sm:w-48">
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
      </div>

      {costCentersQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : costCentersQuery.error ? (
        <ErrorState
          title="Não foi possível carregar os centros de custo"
          description={costCentersQuery.error instanceof Error ? costCentersQuery.error.message : undefined}
          onRetry={() => costCentersQuery.refetch()}
        />
      ) : costCentersQuery.data && costCentersQuery.data.data.length > 0 ? (
        <>
          <CostCentersTable costCenters={costCentersQuery.data.data} />
          <Pagination
            page={costCentersQuery.data.meta.pagination.page}
            limit={costCentersQuery.data.meta.pagination.limit}
            total={costCentersQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={Banknote} title="Nenhum centro de custo encontrado" description="Ajuste a busca/filtro ou crie o primeiro." />
      )}

      <CostCenterFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}
