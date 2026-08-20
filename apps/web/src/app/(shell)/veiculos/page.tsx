"use client";

import * as React from "react";
import { Plus, Truck } from "lucide-react";

import { Button, Input, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { VehicleStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useVehiclesQuery } from "@/modules/fleet/hooks/use-vehicles";
import { VehiclesTable } from "@/modules/fleet/components/vehicles-table";
import { VehicleFormDrawer } from "@/modules/fleet/components/vehicle-form-drawer";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const STATUS_OPTIONS: Array<{ value: "all" | VehicleStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "ATIVO", label: "Ativo" },
  { value: "INATIVO", label: "Inativo" },
];

export default function VehiclesPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [status, setStatus] = React.useState<"all" | VehicleStatus>("all");
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const vehiclesQuery = useVehiclesQuery({ page, limit: 20, search, status: status === "all" ? undefined : status });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Veículos</h1>
          <p className="text-sm text-muted-foreground">Veículos tracionadores da frota.</p>
        </div>
        {hasPermission("fleet.vehicle.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Novo veículo
          </Button>
        ) : null}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          placeholder="Buscar por placa, fabricante ou modelo…"
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
            setStatus(value as "all" | VehicleStatus);
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

      {vehiclesQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : vehiclesQuery.error ? (
        <ErrorState
          title="Não foi possível carregar os veículos"
          description={vehiclesQuery.error instanceof Error ? vehiclesQuery.error.message : undefined}
          onRetry={() => vehiclesQuery.refetch()}
        />
      ) : vehiclesQuery.data && vehiclesQuery.data.data.length > 0 ? (
        <>
          <VehiclesTable vehicles={vehiclesQuery.data.data} />
          <Pagination
            page={vehiclesQuery.data.meta.pagination.page}
            limit={vehiclesQuery.data.meta.pagination.limit}
            total={vehiclesQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={Truck} title="Nenhum veículo encontrado" description="Ajuste a busca/filtro ou crie o primeiro veículo." />
      )}

      <VehicleFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}
