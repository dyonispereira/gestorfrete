"use client";

import * as React from "react";
import { Container, Plus } from "lucide-react";

import { Button, Input, Pagination } from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useImplementsQuery } from "@/modules/fleet/hooks/use-implements";
import { ImplementsTable } from "@/modules/fleet/components/implements-table";
import { ImplementFormDrawer } from "@/modules/fleet/components/implement-form-drawer";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

export default function ImplementsPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const implementsQuery = useImplementsQuery({ page, limit: 20, search });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Implementos</h1>
          <p className="text-sm text-muted-foreground">Carretas e outros implementos da frota.</p>
        </div>
        {hasPermission("fleet.implement.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Novo implemento
          </Button>
        ) : null}
      </div>

      <Input
        placeholder="Buscar por placa…"
        value={search}
        onChange={(event) => {
          setSearch(event.target.value);
          setPage(1);
        }}
        className="sm:max-w-xs"
      />

      {implementsQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : implementsQuery.error ? (
        <ErrorState
          title="Não foi possível carregar os implementos"
          description={implementsQuery.error instanceof Error ? implementsQuery.error.message : undefined}
          onRetry={() => implementsQuery.refetch()}
        />
      ) : implementsQuery.data && implementsQuery.data.data.length > 0 ? (
        <>
          <ImplementsTable implements={implementsQuery.data.data} />
          <Pagination
            page={implementsQuery.data.meta.pagination.page}
            limit={implementsQuery.data.meta.pagination.limit}
            total={implementsQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={Container} title="Nenhum implemento encontrado" description="Ajuste a busca ou crie o primeiro implemento." />
      )}

      <ImplementFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}
