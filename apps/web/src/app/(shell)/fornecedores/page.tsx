"use client";

import * as React from "react";
import { Building2, Plus } from "lucide-react";

import { Button, Input, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { SupplierCategory, SupplierStatus } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useSuppliersQuery } from "@/modules/maintenance/hooks/use-suppliers";
import { SuppliersTable } from "@/modules/maintenance/components/suppliers-table";
import { SupplierFormDrawer } from "@/modules/maintenance/components/supplier-form-drawer";
import { SUPPLIER_CATEGORY_LABEL } from "@/modules/maintenance/components/supplier-category-label";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const STATUS_OPTIONS: Array<{ value: "all" | SupplierStatus; label: string }> = [
  { value: "all", label: "Todos os status" },
  { value: "ATIVO", label: "Ativo" },
  { value: "INATIVO", label: "Inativo" },
];

export default function SuppliersPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [status, setStatus] = React.useState<"all" | SupplierStatus>("all");
  const [category, setCategory] = React.useState<"all" | SupplierCategory>("all");
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const suppliersQuery = useSuppliersQuery({
    page,
    limit: 20,
    search,
    status: status === "all" ? undefined : status,
    category: category === "all" ? undefined : category,
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Fornecedores</h1>
          <p className="text-sm text-muted-foreground">Fornecedores cadastrados.</p>
        </div>
        {hasPermission("maintenance.supplier.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Novo fornecedor
          </Button>
        ) : null}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          placeholder="Buscar por razão social ou CNPJ…"
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
            setStatus(value as "all" | SupplierStatus);
            setPage(1);
          }}
        >
          <SelectTrigger className="sm:w-44">
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
        <Select
          value={category}
          onValueChange={(value) => {
            setCategory(value as "all" | SupplierCategory);
            setPage(1);
          }}
        >
          <SelectTrigger className="sm:w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas as categorias</SelectItem>
            {(Object.keys(SUPPLIER_CATEGORY_LABEL) as SupplierCategory[]).map((value) => (
              <SelectItem key={value} value={value}>
                {SUPPLIER_CATEGORY_LABEL[value]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {suppliersQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : suppliersQuery.error ? (
        <ErrorState
          title="Não foi possível carregar os fornecedores"
          description={suppliersQuery.error instanceof Error ? suppliersQuery.error.message : undefined}
          onRetry={() => suppliersQuery.refetch()}
        />
      ) : suppliersQuery.data && suppliersQuery.data.data.length > 0 ? (
        <>
          <SuppliersTable suppliers={suppliersQuery.data.data} />
          <Pagination
            page={suppliersQuery.data.meta.pagination.page}
            limit={suppliersQuery.data.meta.pagination.limit}
            total={suppliersQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={Building2} title="Nenhum fornecedor encontrado" description="Ajuste a busca/filtro ou crie o primeiro fornecedor." />
      )}

      <SupplierFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}
