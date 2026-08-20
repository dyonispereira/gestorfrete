"use client";

import * as React from "react";
import { Plus, Users as UsersIcon } from "lucide-react";

import { Button, Input, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { EmployeeStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useEmployeesQuery } from "@/modules/identity/hooks/use-employees";
import { EmployeesTable } from "@/modules/identity/components/employees-table";
import { EmployeeFormDrawer } from "@/modules/identity/components/employee-form-drawer";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const STATUS_OPTIONS: Array<{ value: "all" | EmployeeStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "ATIVO", label: "Ativo" },
  { value: "INATIVO", label: "Inativo" },
];

export default function EmployeesPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [status, setStatus] = React.useState<"all" | EmployeeStatus>("all");
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const employeesQuery = useEmployeesQuery({ page, limit: 20, search, status: status === "all" ? undefined : status });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Funcionários</h1>
          <p className="text-sm text-muted-foreground">Funcionários da transportadora.</p>
        </div>
        {hasPermission("identity_access.employee.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Novo funcionário
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
            setStatus(value as "all" | EmployeeStatus);
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

      {employeesQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : employeesQuery.error ? (
        <ErrorState
          title="Não foi possível carregar os funcionários"
          description={employeesQuery.error instanceof Error ? employeesQuery.error.message : undefined}
          onRetry={() => employeesQuery.refetch()}
        />
      ) : employeesQuery.data && employeesQuery.data.data.length > 0 ? (
        <>
          <EmployeesTable employees={employeesQuery.data.data} />
          <Pagination
            page={employeesQuery.data.meta.pagination.page}
            limit={employeesQuery.data.meta.pagination.limit}
            total={employeesQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={UsersIcon} title="Nenhum funcionário encontrado" description="Ajuste a busca/filtro ou crie o primeiro funcionário." />
      )}

      <EmployeeFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}
