"use client";

import * as React from "react";
import { Plus, ShieldCheck } from "lucide-react";

import { Button, Input, Pagination } from "@gestorfrete/ui";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { useRolesQuery } from "@/modules/identity/hooks/use-roles";
import { RolesTable } from "@/modules/identity/components/roles-table";
import { RoleFormDrawer } from "@/modules/identity/components/role-form-drawer";
import { EmptyState } from "@/shared/components/states/empty-state";
import { ErrorState } from "@/shared/components/states/error-state";
import { LoadingState } from "@/shared/components/states/loading-state";

export default function RolesPage() {
  const { hasPermission } = usePermissions();
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  const rolesQuery = useRolesQuery({ page, limit: 20, search });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Papéis</h1>
          <p className="text-sm text-muted-foreground">RBAC — Papéis e as permissões que cada um concede.</p>
        </div>
        {hasPermission("identity_access.role.create") ? (
          <Button onClick={() => setDrawerOpen(true)}>
            <Plus className="h-4 w-4" />
            Novo papel
          </Button>
        ) : null}
      </div>

      <Input
        placeholder="Buscar por nome…"
        value={search}
        onChange={(event) => {
          setSearch(event.target.value);
          setPage(1);
        }}
        className="sm:max-w-xs"
      />

      {rolesQuery.isLoading ? (
        <LoadingState rows={6} />
      ) : rolesQuery.error ? (
        <ErrorState
          title="Não foi possível carregar os papéis"
          description={rolesQuery.error instanceof Error ? rolesQuery.error.message : undefined}
          onRetry={() => rolesQuery.refetch()}
        />
      ) : rolesQuery.data && rolesQuery.data.data.length > 0 ? (
        <>
          <RolesTable roles={rolesQuery.data.data} />
          <Pagination
            page={rolesQuery.data.meta.pagination.page}
            limit={rolesQuery.data.meta.pagination.limit}
            total={rolesQuery.data.meta.pagination.total}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState icon={ShieldCheck} title="Nenhum papel encontrado" description="Ajuste a busca ou crie o primeiro Papel." />
      )}

      <RoleFormDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </div>
  );
}
