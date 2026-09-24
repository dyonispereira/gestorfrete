"use client";

import * as React from "react";
import { Plus, Tags } from "lucide-react";

import { Button, Input, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { VehicleCategoryStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useVehicleCategoriesQuery } from "@/modules/fleet/hooks/use-vehicle-categories";
import { VehicleCategoriesTable } from "@/modules/fleet/components/vehicle-categories-table";
import { VehicleCategoryFormDrawer } from "@/modules/fleet/components/vehicle-category-form-drawer";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const STATUS_OPTIONS: Array<{ value: "all" | VehicleCategoryStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "ATIVA", label: "Ativa" },
  { value: "INATIVA", label: "Inativa" },
];

export default function VehicleCategoriesPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [status, setStatus] = React.useState<"all" | VehicleCategoryStatus>("all");
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const categoriesQuery = useVehicleCategoriesQuery({
    page, limit: 20, search, status: status === "all" ? undefined : status,
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Categorias de Veículo</h1>
          <p className="text-sm text-muted-foreground">
            Classificação usada no cadastro de Veículos e Implementos (D363).
          </p>
        </div>
        {hasPermission("fleet.vehicle_category.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Nova categoria
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
            setStatus(value as "all" | VehicleCategoryStatus);
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

      {categoriesQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : categoriesQuery.error ? (
        <ErrorState
          title="Não foi possível carregar as categorias"
          description={categoriesQuery.error instanceof Error ? categoriesQuery.error.message : undefined}
          onRetry={() => categoriesQuery.refetch()}
        />
      ) : categoriesQuery.data && categoriesQuery.data.data.length > 0 ? (
        <>
          <VehicleCategoriesTable categories={categoriesQuery.data.data} />
          <Pagination
            page={categoriesQuery.data.meta.pagination.page}
            limit={categoriesQuery.data.meta.pagination.limit}
            total={categoriesQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={Tags} title="Nenhuma categoria encontrada" description="Ajuste a busca/filtro ou crie a primeira." />
      )}

      <VehicleCategoryFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}
