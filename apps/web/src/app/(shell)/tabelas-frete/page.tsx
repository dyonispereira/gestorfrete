"use client";

import * as React from "react";
import { Plus, Tags } from "lucide-react";

import { Button, Pagination, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@gestorfrete/ui";
import type { PriceTableDirection } from "@gestorfrete/types";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { usePriceTablesQuery } from "@/modules/pricing/hooks/use-price-tables";
import { PriceTablesTable } from "@/modules/pricing/components/price-tables-table";
import { PriceTableFormDrawer } from "@/modules/pricing/components/price-table-form-drawer";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

const DIRECTION_OPTIONS: Array<{ value: "all" | PriceTableDirection; label: string }> = [
  { value: "all", label: "Todas as direções" },
  { value: "VENDA", label: "Venda" },
  { value: "COMPRA", label: "Compra" },
];

export default function PriceTablesPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [direcao, setDirecao] = React.useState<"all" | PriceTableDirection>("all");
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const priceTablesQuery = usePriceTablesQuery({
    page, limit: 20, direcao: direcao === "all" ? undefined : direcao,
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Tabelas de Frete</h1>
          <p className="text-sm text-muted-foreground">Tabelas de venda (cliente) e compra (transportador).</p>
        </div>
        {hasPermission("pricing.price_table.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Nova tabela
          </Button>
        ) : null}
      </div>

      <Select
        value={direcao}
        onValueChange={(value) => {
          setDirecao(value as "all" | PriceTableDirection);
          setPage(1);
        }}
      >
        <SelectTrigger className="sm:w-56">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {DIRECTION_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {priceTablesQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : priceTablesQuery.error ? (
        <ErrorState
          title="Não foi possível carregar as tabelas de frete"
          description={priceTablesQuery.error instanceof Error ? priceTablesQuery.error.message : undefined}
          onRetry={() => priceTablesQuery.refetch()}
        />
      ) : priceTablesQuery.data && priceTablesQuery.data.data.length > 0 ? (
        <>
          <PriceTablesTable priceTables={priceTablesQuery.data.data} />
          <Pagination
            page={priceTablesQuery.data.meta.pagination.page}
            limit={priceTablesQuery.data.meta.pagination.limit}
            total={priceTablesQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={Tags} title="Nenhuma tabela de frete encontrada" description="Crie a primeira tabela de venda ou compra." />
      )}

      <PriceTableFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}
