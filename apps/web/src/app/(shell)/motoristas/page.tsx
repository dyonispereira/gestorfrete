"use client";

import * as React from "react";
import { Plus, Truck } from "lucide-react";

import { Button, Input, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { DriverEmploymentType } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useDriversQuery } from "@/modules/drivers/hooks/use-drivers";
import { DriversTable } from "@/modules/drivers/components/drivers-table";
import { DriverFormDrawer } from "@/modules/drivers/components/driver-form-drawer";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const EMPLOYMENT_OPTIONS: Array<{ value: "all" | DriverEmploymentType; label: string }> = [
  { value: "all", label: "Todos os vínculos" },
  { value: "EMPREGADO", label: "Empregado" },
  { value: "AUTONOMO", label: "Autônomo" },
];

export default function DriversPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [employmentType, setEmploymentType] = React.useState<"all" | DriverEmploymentType>("all");
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const driversQuery = useDriversQuery({
    page,
    limit: 20,
    search,
    employment_type: employmentType === "all" ? undefined : employmentType,
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Motoristas</h1>
          <p className="text-sm text-muted-foreground">Motoristas da frota.</p>
        </div>
        {hasPermission("drivers.driver.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Novo motorista
          </Button>
        ) : null}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          placeholder="Buscar por nome ou CPF…"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPage(1);
          }}
          className="sm:max-w-xs"
        />
        <Select
          value={employmentType}
          onValueChange={(value) => {
            setEmploymentType(value as "all" | DriverEmploymentType);
            setPage(1);
          }}
        >
          <SelectTrigger className="sm:w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {EMPLOYMENT_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {driversQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : driversQuery.error ? (
        <ErrorState
          title="Não foi possível carregar os motoristas"
          description={driversQuery.error instanceof Error ? driversQuery.error.message : undefined}
          onRetry={() => driversQuery.refetch()}
        />
      ) : driversQuery.data && driversQuery.data.data.length > 0 ? (
        <>
          <DriversTable drivers={driversQuery.data.data} />
          <Pagination
            page={driversQuery.data.meta.pagination.page}
            limit={driversQuery.data.meta.pagination.limit}
            total={driversQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={Truck} title="Nenhum motorista encontrado" description="Ajuste a busca/filtro ou crie o primeiro motorista." />
      )}

      <DriverFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}
